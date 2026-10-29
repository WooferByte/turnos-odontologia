import { describe, expect, it } from 'vitest'
import { crearClienteHttp } from '../../shared/api/clienteHttp'
import { RecursoInexistente, SinConexion } from '../../shared/api/errores'
import { crearSesion } from '../../shared/api/sesion'
import {
  EMAIL_RECEPCIONISTA,
  EVENTO_CREADO_DEL_TURNO_11,
  TURNOS_DE_LA_AGENDA,
  crearServidorFalso,
  type ServidorFalso,
} from '../../test/servidorFalso'
import { crearApiHistorial } from './apiHistorial'

function apiConSesion(servidor: ServidorFalso) {
  const sesion = crearSesion(null)
  const { access, refresh } = servidor.emitirSesion(EMAIL_RECEPCIONISTA)
  sesion.guardar(access, refresh)
  const cliente = crearClienteHttp({ fetch: servidor.fetch, sesion })
  return crearApiHistorial(cliente.pedidoDelPanel)
}

describe('apiHistorial', () => {
  it('HIS-2a: obtenerHistorial devuelve los eventos del turno', async () => {
    const servidor = crearServidorFalso({ turnos: TURNOS_DE_LA_AGENDA, historiales: { 11: [EVENTO_CREADO_DEL_TURNO_11] } })
    const api = apiConSesion(servidor)

    const eventos = await api.obtenerHistorial(11)

    expect(eventos).toEqual([EVENTO_CREADO_DEL_TURNO_11])
    expect(servidor.peticiones('/api/turnos/11/historial')).toBe(1)
  })

  it('HIS-2c: un turno sin eventos devuelve una lista vacía', async () => {
    const api = apiConSesion(crearServidorFalso({ turnos: TURNOS_DE_LA_AGENDA }))

    expect(await api.obtenerHistorial(12)).toEqual([])
  })

  it('HIS-2d: un 404 da RecursoInexistente con RN-GL-04', async () => {
    const api = apiConSesion(crearServidorFalso({ turnos: TURNOS_DE_LA_AGENDA }))

    const rechazo = await api.obtenerHistorial(99).catch((e: unknown) => e)

    expect(rechazo).toBeInstanceOf(RecursoInexistente)
    expect((rechazo as RecursoInexistente).codigo).toBe('RN-GL-04')
  })

  it('G8: una respuesta de otra forma es SinConexion', async () => {
    const servidor = crearServidorFalso({ turnos: TURNOS_DE_LA_AGENDA })
    servidor.fallarRuta('/api/turnos/11/historial', { cuerpo: [{ id: 1, tipo: 'creado' }] })
    const api = apiConSesion(servidor)

    const rechazo = await api.obtenerHistorial(11).catch((e: unknown) => e)

    expect(rechazo).toBeInstanceOf(SinConexion)
  })
})
