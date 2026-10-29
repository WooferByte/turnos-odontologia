import { describe, expect, it } from 'vitest'
import { crearClienteHttp } from '../../shared/api/clienteHttp'
import { EntradaRechazada, RecursoInexistente, ReglaRechazada } from '../../shared/api/errores'
import { crearSesion } from '../../shared/api/sesion'
import {
  EMAIL_RECEPCIONISTA,
  PRESTACIONES_DE_PARTIDA,
  TURNOS_DE_LA_AGENDA,
  crearServidorFalso,
  type ServidorFalso,
} from '../../test/servidorFalso'
import { crearApiAgenda } from './apiAgenda'

function apiConSesion(servidor: ServidorFalso) {
  const sesion = crearSesion(null)
  const { access, refresh } = servidor.emitirSesion(EMAIL_RECEPCIONISTA)
  sesion.guardar(access, refresh)
  const cliente = crearClienteHttp({ fetch: servidor.fetch, sesion })
  return crearApiAgenda(cliente.pedidoDelPanel)
}

const NUEVO = { paciente_id: 2, prestacion_id: 2, inicio: '2026-11-02T13:00:00Z' }

describe('apiAgenda', () => {
  it('AGE-4a: obtenerAgenda sin fecha devuelve el día de hoy con sus turnos', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA, turnos: TURNOS_DE_LA_AGENDA })
    const api = apiConSesion(servidor)

    const agenda = await api.obtenerAgenda()

    expect(agenda.fecha).toBe('2026-11-02')
    expect(agenda.zona_horaria).toBe('America/Argentina/Buenos_Aires')
    expect(agenda.turnos.map((t) => [t.paciente.apellido, t.prestacion.nombre, t.prestacion.color, t.estado])).toEqual([
      ['Ejemplo', 'Consulta / control', '#1E88E5', 'reservado'],
      ['Ficticio', 'Limpieza', '#43A047', 'reservado'],
      ['Inventada', 'Obturación', '#FB8C00', 'confirmado'],
    ])
    expect(servidor.peticiones('/api/turnos')).toBe(1)
  })

  it('AGE-4b: obtenerAgenda con fecha la manda en la ruta y devuelve ese día', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA, turnos: TURNOS_DE_LA_AGENDA })
    const api = apiConSesion(servidor)

    const agenda = await api.obtenerAgenda('2026-11-03')

    expect(agenda).toMatchObject({ fecha: '2026-11-03', turnos: [] })
    expect(servidor.peticiones('/api/turnos?fecha=2026-11-03')).toBe(1)
  })

  it('AGE-5a: crearTurno manda paciente, prestación e inicio en UTC', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const api = apiConSesion(servidor)

    const creado = await api.crearTurno(NUEVO)

    expect(servidor.cuerpos('POST', '/api/turnos')).toEqual([NUEVO])
    expect(creado).toMatchObject({ paciente_id: 2, prestacion_id: 2, inicio: '2026-11-02T13:00:00Z', fin: '2026-11-02T13:45:00Z' })
    expect(servidor.turnosActuales().map((t) => t.estado)).toEqual(['reservado'])
  })

  it('AGE-5c: un 409 de E4 trae los dos códigos', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA, turnos: TURNOS_DE_LA_AGENDA })
    const api = apiConSesion(servidor)

    const rechazo = await api.crearTurno({ paciente_id: 2, prestacion_id: 1, inicio: '2026-11-02T12:00:00Z' }).catch((e: unknown) => e)

    expect(rechazo).toBeInstanceOf(ReglaRechazada)
    expect((rechazo as ReglaRechazada).codigo).toBe('RN-AG-05')
    expect((rechazo as ReglaRechazada).codigos).toEqual(['RN-AG-05', 'RN-AG-08'])
  })

  it('AGE-5d: un 422 de E12 trae las referencias', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const api = apiConSesion(servidor)

    const rechazo = await api.crearTurno({ paciente_id: 99, prestacion_id: 5, inicio: '2026-11-02T13:00:00Z' }).catch((e: unknown) => e)

    expect(rechazo).toBeInstanceOf(EntradaRechazada)
    expect((rechazo as EntradaRechazada).codigos).toEqual(['RN-GL-04'])
    expect((rechazo as EntradaRechazada).referencias).toEqual([
      { recurso: 'paciente', recurso_id: 99, motivo: 'inexistente' },
      { recurso: 'prestacion', recurso_id: 5, motivo: 'inactivo' },
    ])
  })

  it('AGE-5a: obtenerPrestacionesActivas devuelve solo las activas', async () => {
    const api = apiConSesion(crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA }))

    const activas = await api.obtenerPrestacionesActivas()

    expect(activas.map((p) => p.nombre)).toEqual(['Consulta / control', 'Limpieza', 'Obturación', 'Extracción'])
  })

  it('REP-6a: reprogramarTurno manda inicio y duración y devuelve el turno', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA, turnos: TURNOS_DE_LA_AGENDA })
    const api = apiConSesion(servidor)

    const movido = await api.reprogramarTurno(11, { inicio: '2026-11-02T15:30:00Z', duracion_minutos: 30 })

    expect(servidor.cuerpos('PATCH', '/api/turnos/11')).toEqual([{ inicio: '2026-11-02T15:30:00Z', duracion_minutos: 30 }])
    expect(movido).toMatchObject({ id: 11, inicio: '2026-11-02T15:30:00Z', fin: '2026-11-02T16:00:00Z' })
    expect(servidor.turnosActuales().find((t) => t.id === 11)?.inicio).toBe('2026-11-02T15:30:00Z')
  })

  it('REP-6a: reprogramarTurno con otra duración devuelve el fin nuevo', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA, turnos: TURNOS_DE_LA_AGENDA })
    const api = apiConSesion(servidor)

    const movido = await api.reprogramarTurno(13, { inicio: '2026-11-02T14:00:00Z', duracion_minutos: 90 })

    expect(movido).toMatchObject({ id: 13, fin: '2026-11-02T15:30:00Z', duracion_minutos: 90 })
  })

  it('REP-7a: un 409 de REP-1 trae los dos códigos', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA, turnos: TURNOS_DE_LA_AGENDA })
    const api = apiConSesion(servidor)

    const rechazo = await api.reprogramarTurno(11, { inicio: '2026-11-02T13:15:00Z', duracion_minutos: 30 }).catch((e: unknown) => e)

    expect(rechazo).toBeInstanceOf(ReglaRechazada)
    expect((rechazo as ReglaRechazada).codigos).toEqual(['RN-AG-05', 'RN-AG-08'])
    expect(servidor.turnosActuales().find((t) => t.id === 11)?.inicio).toBe('2026-11-02T12:00:00Z')
  })

  it('REP-7b: un 409 de RN-AG-18 es una regla rechazada con su código', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA, turnos: TURNOS_DE_LA_AGENDA })
    servidor.responderAlReprogramar(409, ['RN-AG-18'])
    const api = apiConSesion(servidor)

    const rechazo = await api.reprogramarTurno(11, { inicio: '2026-11-02T15:30:00Z', duracion_minutos: 30 }).catch((e: unknown) => e)

    expect(rechazo).toBeInstanceOf(ReglaRechazada)
    expect((rechazo as ReglaRechazada).codigo).toBe('RN-AG-18')
  })

  it('REP-7b: un 404 de un turno que no está es un recurso inexistente', async () => {
    const api = apiConSesion(crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA, turnos: TURNOS_DE_LA_AGENDA }))

    const rechazo = await api.reprogramarTurno(99, { inicio: '2026-11-02T15:30:00Z', duracion_minutos: 30 }).catch((e: unknown) => e)

    expect(rechazo).toBeInstanceOf(RecursoInexistente)
  })
})
