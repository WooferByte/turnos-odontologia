import { describe, expect, it } from 'vitest'
import { crearClienteHttp } from '../../shared/api/clienteHttp'
import { EntradaRechazada, PermisoInsuficiente, RecursoInexistente } from '../../shared/api/errores'
import { crearSesion } from '../../shared/api/sesion'
import {
  BLOQUEO_DE_VACACIONES,
  BLOQUEO_FERIADO,
  EMAIL_ACTIVA,
  EMAIL_RECEPCIONISTA,
  SILLON_INACTIVO,
  SILLONES_DE_PARTIDA,
  TURNOS_DEL_2_DE_NOVIEMBRE,
  ZONA_DEL_CONSULTORIO,
  crearServidorFalso,
  type ServidorFalso,
} from '../../test/servidorFalso'
import { crearApiBloqueos } from './apiBloqueos'

function apiConSesion(servidor: ServidorFalso, email: string = EMAIL_ACTIVA) {
  const sesion = crearSesion(null)
  const { access, refresh } = servidor.emitirSesion(email)
  sesion.guardar(access, refresh)
  const cliente = crearClienteHttp({ fetch: servidor.fetch, sesion })
  return crearApiBloqueos(cliente.pedidoDelPanel)
}

const FERIADO = { inicio: '2026-11-23T03:00:00Z', fin: '2026-11-24T03:00:00Z', motivo: 'Feriado' }

describe('apiBloqueos', () => {
  it('US-003 CA-1: listar devuelve la zona y los bloqueos', async () => {
    const servidor = crearServidorFalso({ bloqueos: [BLOQUEO_FERIADO, BLOQUEO_DE_VACACIONES] })
    const api = apiConSesion(servidor)

    const lista = await api.listarBloqueos()

    expect(lista.zona_horaria).toBe(ZONA_DEL_CONSULTORIO)
    expect(lista.bloqueos.map((b) => [b.id, b.alcance, b.motivo])).toEqual([
      [1, 'profesional', 'Vacaciones'],
      [2, 'consultorio', 'Feriado'],
    ])
    expect(servidor.llamadas('GET', '/api/bloqueos')).toBe(1)
  })

  it('US-003 CA-2: crear devuelve el bloqueo y los turnos afectados', async () => {
    const servidor = crearServidorFalso({ turnos: TURNOS_DEL_2_DE_NOVIEMBRE })
    const api = apiConSesion(servidor)

    const creado = await api.crearBloqueo({
      profesional_id: 1,
      inicio: '2026-11-02T12:00:00Z',
      fin: '2026-11-02T16:00:00Z',
      motivo: 'Ausencia',
    })

    expect(creado.alcance).toBe('profesional')
    expect(creado.turnos_afectados.map((t) => [t.id, t.estado])).toEqual([
      [7, 'reservado'],
      [8, 'confirmado'],
    ])
    expect(servidor.bloqueosActuales()).toHaveLength(1)
  })

  it('US-003 CA-1: un bloqueo invertido levanta EntradaRechazada con RN-AG-17', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor)

    const rechazo = await api.crearBloqueo({ ...FERIADO, inicio: FERIADO.fin, fin: FERIADO.inicio }).catch((e: unknown) => e)

    expect(rechazo).toBeInstanceOf(EntradaRechazada)
    expect((rechazo as EntradaRechazada).codigos).toEqual(['RN-AG-17'])
    expect(servidor.bloqueosActuales()).toEqual([])
  })

  it('US-003 CA-1: eliminar responde sin cuerpo', async () => {
    const servidor = crearServidorFalso({ bloqueos: [BLOQUEO_FERIADO] })
    const api = apiConSesion(servidor)

    await expect(api.eliminarBloqueo(2)).resolves.toBeUndefined()

    expect(servidor.llamadas('DELETE', '/api/bloqueos/2')).toBe(1)
    expect(servidor.bloqueosActuales()).toEqual([])
  })

  it('US-003 CA-1: la recepcionista que crea recibe PermisoInsuficiente', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor, EMAIL_RECEPCIONISTA)

    const rechazo = await api.crearBloqueo(FERIADO).catch((e: unknown) => e)

    expect(rechazo).toBeInstanceOf(PermisoInsuficiente)
    expect((rechazo as PermisoInsuficiente).codigo).toBe('RN-AU-05')
    expect(servidor.bloqueosActuales()).toEqual([])
  })

  it('US-003 CA-1: un bloqueo inexistente al eliminar levanta RecursoInexistente con RN-GL-04', async () => {
    const api = apiConSesion(crearServidorFalso())

    const rechazo = await api.eliminarBloqueo(99).catch((e: unknown) => e)

    expect(rechazo).toBeInstanceOf(RecursoInexistente)
    expect((rechazo as RecursoInexistente).codigo).toBe('RN-GL-04')
  })

  it('US-003 CA-1: listar sillones devuelve los de la demo y el inactivo', async () => {
    const servidor = crearServidorFalso({ sillones: [...SILLONES_DE_PARTIDA, SILLON_INACTIVO] })
    const api = apiConSesion(servidor)

    expect(await api.listarSillones()).toEqual([
      { id: 1, nombre: 'Sillón 1', activo: true },
      { id: 2, nombre: 'Sillón 2', activo: false },
    ])
  })
})
