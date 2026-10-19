import { describe, expect, it } from 'vitest'
import { crearClienteHttp } from '../../shared/api/clienteHttp'
import {
  EntradaRechazada,
  PermisoInsuficiente,
  RecursoInexistente,
  ReglaRechazada,
  SinConexion,
} from '../../shared/api/errores'
import { crearSesion } from '../../shared/api/sesion'
import {
  EMAIL_ACTIVA,
  EMAIL_RECEPCIONISTA,
  PRESTACIONES_DE_PARTIDA,
  crearServidorFalso,
  type ServidorFalso,
} from '../../test/servidorFalso'
import { cambiosEntre, crearApiPrestaciones, type Prestacion } from './apiPrestaciones'

function apiConSesion(servidor: ServidorFalso, email: string = EMAIL_ACTIVA) {
  const sesion = crearSesion(null)
  const { access, refresh } = servidor.emitirSesion(email)
  sesion.guardar(access, refresh)
  const cliente = crearClienteHttp({ fetch: servidor.fetch, sesion })
  return crearApiPrestaciones(cliente.pedidoDelPanel)
}

function conSesion(servidor: ServidorFalso, email: string) {
  const sesion = crearSesion(null)
  const { access, refresh } = servidor.emitirSesion(email)
  sesion.guardar(access, refresh)
  const cliente = crearClienteHttp({ fetch: servidor.fetch, sesion })
  return { api: crearApiPrestaciones(cliente.pedidoDelPanel), sesion }
}

const LIMPIEZA: Prestacion = {
  id: 2,
  nombre: 'Limpieza',
  duracion_minutos: 45,
  color: '#43A047',
  reservable_online: false,
  activa: true,
}
const DATOS_VALIDOS = { nombre: 'Blanqueamiento', duracion_minutos: 60, color: '#3A7BD5', reservable_online: false }

describe('apiPrestaciones', () => {
  it('US-001 CA-1: listar devuelve las prestaciones en orden de id', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const api = apiConSesion(servidor)

    const lista = await api.listarPrestaciones()

    expect(lista.map((p) => p.id)).toEqual([1, 2, 3, 4, 5])
    expect(lista[1]).toEqual({
      id: 2,
      nombre: 'Limpieza',
      duracion_minutos: 45,
      color: '#43A047',
      reservable_online: false,
      activa: true,
    })
    expect(servidor.llamadas('GET', '/api/prestaciones')).toBe(1)
  })

  it('US-001 CA-1: crear devuelve la prestación nueva', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const api = apiConSesion(servidor)

    const nueva = await api.crearPrestacion({
      nombre: 'Blanqueamiento',
      duracion_minutos: 60,
      color: '#3A7BD5',
      reservable_online: false,
    })

    expect(nueva).toEqual({
      id: 6,
      nombre: 'Blanqueamiento',
      duracion_minutos: 60,
      color: '#3A7BD5',
      reservable_online: false,
      activa: true,
    })
    expect(servidor.cuerpos('POST', '/api/prestaciones')).toEqual([
      { nombre: 'Blanqueamiento', duracion_minutos: 60, color: '#3A7BD5', reservable_online: false },
    ])
  })

  it('US-001 CA-1: nombre repetido levanta ReglaRechazada con RN-AG-15', async () => {
    const api = apiConSesion(crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA }))

    const error = await api
      .crearPrestacion({ nombre: 'limpieza', duracion_minutos: 45, color: '#43A047', reservable_online: false })
      .catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ReglaRechazada)
    expect((error as ReglaRechazada).codigo).toBe('RN-AG-15')
  })

  it('US-001 CA-2: duración 47 levanta EntradaRechazada con el error de campo RN-AG-01', async () => {
    const api = apiConSesion(crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA }))

    const error = await api
      .crearPrestacion({ nombre: 'Blanqueamiento', duracion_minutos: 47, color: '#3A7BD5', reservable_online: false })
      .catch((e: unknown) => e)

    expect(error).toBeInstanceOf(EntradaRechazada)
    const rechazo = error as EntradaRechazada
    expect(rechazo.codigos).toEqual(['RN-AG-01'])
    expect(rechazo.errores.map((e) => [e.campo, e.codigo])).toEqual([['duracion_minutos', 'RN-AG-01']])
  })

  it('US-001 CA-1: editar manda solo los campos cambiados (el registro del falso tiene solo color)', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const api = apiConSesion(servidor)

    const editada = await api.editarPrestacion(2, cambiosEntre(LIMPIEZA, { ...LIMPIEZA, color: '#F9A825' }))

    expect(servidor.cuerpos('PATCH', '/api/prestaciones/2')).toEqual([{ color: '#F9A825' }])
    expect(editada).toEqual({ ...LIMPIEZA, color: '#F9A825' })
  })

  it('US-001 CA-1: cambiosEntre detecta un cambio solo de mayúsculas y no manda lo igual', () => {
    expect(cambiosEntre(LIMPIEZA, { ...LIMPIEZA, nombre: 'LIMPIEZA' })).toEqual({ nombre: 'LIMPIEZA' })
    expect(cambiosEntre(LIMPIEZA, { ...LIMPIEZA })).toEqual({})
    expect(cambiosEntre(LIMPIEZA, { ...LIMPIEZA, duracion_minutos: 60, activa: false })).toEqual({
      duracion_minutos: 60,
      activa: false,
    })
  })

  it('US-001 CA-1: id inexistente levanta RecursoInexistente con RN-GL-04', async () => {
    const api = apiConSesion(crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA }))

    const error = await api.editarPrestacion(99, { color: '#F9A825' }).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(RecursoInexistente)
    expect((error as RecursoInexistente).codigo).toBe('RN-GL-04')
  })

  it('US-001 CA-1: la recepcionista recibe PermisoInsuficiente con RN-AU-05 y la sesión sigue', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const { api, sesion } = conSesion(servidor, EMAIL_RECEPCIONISTA)

    const error = await api.crearPrestacion(DATOS_VALIDOS).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(PermisoInsuficiente)
    expect((error as PermisoInsuficiente).codigo).toBe('RN-AU-05')
    expect(sesion.refresh()).not.toBeNull()
    expect(servidor.peticiones('/api/auth/refresh')).toBe(0)
    expect((await api.listarPrestaciones()).length).toBe(5)
  })

  it('US-001 CA-1: la recepcionista con duración 47 recibe PermisoInsuficiente y no EntradaRechazada', async () => {
    const { api } = conSesion(crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA }), EMAIL_RECEPCIONISTA)

    const error = await api.crearPrestacion({ ...DATOS_VALIDOS, duracion_minutos: 47 }).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(PermisoInsuficiente)
    expect(error).not.toBeInstanceOf(EntradaRechazada)
  })

  it('US-001 CA-1: nombre solo de espacios levanta EntradaRechazada con error del campo nombre y codigos vacío', async () => {
    const api = apiConSesion(crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA }))

    const error = await api.crearPrestacion({ ...DATOS_VALIDOS, nombre: '   ' }).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(EntradaRechazada)
    const rechazo = error as EntradaRechazada
    expect(rechazo.codigos).toEqual([])
    expect(rechazo.errores.map((e) => [e.campo, e.codigo])).toEqual([['nombre', null]])
  })

  it('US-001 CA-2: duración 0 y -5 levantan RN-AG-01', async () => {
    const api = apiConSesion(crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA }))

    for (const duracion of [0, -5]) {
      const error = await api.crearPrestacion({ ...DATOS_VALIDOS, duracion_minutos: duracion }).catch((e: unknown) => e)
      expect(error).toBeInstanceOf(EntradaRechazada)
      expect((error as EntradaRechazada).codigos).toEqual(['RN-AG-01'])
    }
  })

  it('US-001 CA-1: un 5xx o la red caída levantan SinConexion', async () => {
    const con5xx = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const api5xx = apiConSesion(con5xx)
    con5xx.responderConError(503)
    const caido = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const apiCaida = apiConSesion(caido)
    caido.caerse()

    expect(await api5xx.listarPrestaciones().catch((e: unknown) => e)).toBeInstanceOf(SinConexion)
    expect(await apiCaida.crearPrestacion(DATOS_VALIDOS).catch((e: unknown) => e)).toBeInstanceOf(SinConexion)
  })
})
