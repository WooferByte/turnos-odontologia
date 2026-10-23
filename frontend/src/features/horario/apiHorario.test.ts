import { describe, expect, it } from 'vitest'
import { crearClienteHttp } from '../../shared/api/clienteHttp'
import { EntradaRechazada, PermisoInsuficiente, RecursoInexistente } from '../../shared/api/errores'
import { crearSesion } from '../../shared/api/sesion'
import {
  EMAIL_ACTIVA,
  EMAIL_RECEPCIONISTA,
  HORARIO_DE_LA_DEMO,
  PROFESIONAL_INACTIVO,
  PROFESIONALES_DE_PARTIDA,
  ZONA_DEL_CONSULTORIO,
  crearServidorFalso,
  type ServidorFalso,
} from '../../test/servidorFalso'
import { crearApiHorario, type Franja } from './apiHorario'

function apiConSesion(servidor: ServidorFalso, email: string = EMAIL_ACTIVA) {
  const sesion = crearSesion(null)
  const { access, refresh } = servidor.emitirSesion(email)
  sesion.guardar(access, refresh)
  const cliente = crearClienteHttp({ fetch: servidor.fetch, sesion })
  return crearApiHorario(cliente.pedidoDelPanel)
}

const SABADO: Franja = { dia_semana: 5, hora_inicio: '09:00', hora_fin: '12:00' }

describe('apiHorario', () => {
  it('US-002 CA-1: obtener devuelve las franjas y la zona', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor)

    const horario = await api.obtenerHorario(1)

    expect(horario.profesional_id).toBe(1)
    expect(horario.zona_horaria).toBe(ZONA_DEL_CONSULTORIO)
    expect(horario.franjas).toEqual(HORARIO_DE_LA_DEMO)
    expect(servidor.llamadas('GET', '/api/profesionales/1/horario')).toBe(1)
  })

  it('US-002 CA-1: reemplazar devuelve el horario guardado', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor)

    const guardado = await api.reemplazarHorario(1, [...HORARIO_DE_LA_DEMO, SABADO])

    expect(guardado.franjas).toHaveLength(11)
    expect(guardado.franjas[10]).toEqual(SABADO)
    expect(servidor.cuerpos('PUT', '/api/profesionales/1/horario')).toEqual([{ franjas: [...HORARIO_DE_LA_DEMO, SABADO] }])
    expect(servidor.horarioActual(1)).toHaveLength(11)
  })

  it('HOR-1: franjas superpuestas levantan EntradaRechazada con los errores de franjas.<i> y RN-AG-16', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor)
    const solapada: Franja = { dia_semana: 2, hora_inicio: '12:00', hora_fin: '16:00' }

    const error = await api.reemplazarHorario(1, [...HORARIO_DE_LA_DEMO, solapada]).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(EntradaRechazada)
    const rechazo = error as EntradaRechazada
    expect(rechazo.codigo).toBe('RN-AG-16')
    // Solo la posterior de cada par se informa (H6): la 12:00-16:00 agregada al final del cuerpo.
    expect(rechazo.errores.map((e) => [e.campo, e.codigo])).toEqual([['franjas.10', 'RN-AG-16']])
    expect(servidor.horarioActual(1)).toEqual(HORARIO_DE_LA_DEMO)
  })

  it('US-002 CA-1: listar profesionales devuelve activos e inactivos', async () => {
    const servidor = crearServidorFalso({ profesionales: [...PROFESIONALES_DE_PARTIDA, PROFESIONAL_INACTIVO] })
    const api = apiConSesion(servidor)

    const profesionales = await api.listarProfesionales()

    expect(profesionales).toEqual([
      { id: 1, nombre: 'Dra. Demo Ficticia', activo: true },
      { id: 2, nombre: 'Dr. Ejemplo Ficticio', activo: false },
    ])
    expect(servidor.llamadas('GET', '/api/profesionales')).toBe(1)
  })

  it('US-002 CA-1: la recepcionista que reemplaza recibe PermisoInsuficiente', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor, EMAIL_RECEPCIONISTA)

    const error = await api.reemplazarHorario(1, [SABADO]).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(PermisoInsuficiente)
    expect((error as PermisoInsuficiente).codigo).toBe('RN-AU-05')
    expect(servidor.horarioActual(1)).toEqual(HORARIO_DE_LA_DEMO)
    expect((await api.obtenerHorario(1)).franjas).toHaveLength(10)
  })

  it('US-002 CA-1: un profesional inexistente levanta RecursoInexistente con RN-GL-04', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor)

    const enLectura = await api.obtenerHorario(99).catch((e: unknown) => e)
    const enReemplazo = await api.reemplazarHorario(99, [SABADO]).catch((e: unknown) => e)

    for (const error of [enLectura, enReemplazo]) {
      expect(error).toBeInstanceOf(RecursoInexistente)
      expect((error as RecursoInexistente).codigo).toBe('RN-GL-04')
    }
  })

  it('US-002 CA-1: más de 70 franjas levantan EntradaRechazada sin códigos', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor)
    const sinSolapar = (n: number): Franja[] =>
      Array.from({ length: n }, (_, i) => ({
        dia_semana: i % 7,
        hora_inicio: `${String(Math.floor(i / 7)).padStart(2, '0')}:00`,
        hora_fin: `${String(Math.floor(i / 7)).padStart(2, '0')}:30`,
      }))

    const error = await api.reemplazarHorario(1, sinSolapar(71)).catch((e: unknown) => e)
    const aceptado = await api.reemplazarHorario(1, sinSolapar(70))

    expect(error).toBeInstanceOf(EntradaRechazada)
    expect((error as EntradaRechazada).codigos).toEqual([])
    expect((error as EntradaRechazada).errores.map((e) => e.campo)).toEqual(['franjas'])
    expect(aceptado.franjas).toHaveLength(70)
  })
})
