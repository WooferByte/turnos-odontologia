import { describe, expect, it } from 'vitest'
import { crearClienteHttp } from '../../shared/api/clienteHttp'
import { SesionTerminada, SinConexion } from '../../shared/api/errores'
import { crearSesion } from '../../shared/api/sesion'
import { EMAIL_ACTIVA, EMAIL_RECEPCIONISTA, crearServidorFalso, type ServidorFalso } from '../../test/servidorFalso'
import { obtenerUsuarioDeLaSesion } from './apiSesion'

const RUTA = '/api/auth/yo'

function pedidoConSesion(servidor: ServidorFalso, email: string = EMAIL_ACTIVA) {
  const sesion = crearSesion(null)
  const { access, refresh } = servidor.emitirSesion(email)
  sesion.guardar(access, refresh)
  return crearClienteHttp({ fetch: servidor.fetch, sesion }).pedidoDelPanel
}

describe('apiSesion', () => {
  it('SES-4a: obtenerUsuarioDeLaSesion devuelve el email y los roles', async () => {
    const servidor = crearServidorFalso()

    const usuario = await obtenerUsuarioDeLaSesion(pedidoConSesion(servidor))

    expect(usuario).toEqual({ email: EMAIL_ACTIVA, roles: ['odontologo', 'dueno'] })
    expect(servidor.llamadas('GET', RUTA)).toBe(1)
  })

  it('SES-4a: con otro usuario devuelve los datos de ese usuario', async () => {
    const servidor = crearServidorFalso()

    const usuario = await obtenerUsuarioDeLaSesion(pedidoConSesion(servidor, EMAIL_RECEPCIONISTA))

    expect(usuario).toEqual({ email: EMAIL_RECEPCIONISTA, roles: ['recepcionista'] })
  })

  it('SES-4h: un 403 devuelve null', async () => {
    const servidor = crearServidorFalso()
    servidor.quitarPermiso(EMAIL_ACTIVA)

    const usuario = await obtenerUsuarioDeLaSesion(pedidoConSesion(servidor))

    expect(usuario).toBeNull()
    expect(servidor.llamadas('GET', RUTA)).toBe(1)
  })

  it('SES-5a: un 401 sin renovación posible levanta SesionTerminada', async () => {
    const servidor = crearServidorFalso()
    const pedido = pedidoConSesion(servidor)
    servidor.vencerAccess()
    servidor.invalidarRefresh()

    const error = await obtenerUsuarioDeLaSesion(pedido).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(SesionTerminada)
    expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(1)
  })

  it('SES-4i: una respuesta con un rol desconocido devuelve null', async () => {
    const servidor = crearServidorFalso()
    servidor.fallarRuta(RUTA, { cuerpo: { email: EMAIL_ACTIVA, roles: ['administrador'] } })

    const usuario = await obtenerUsuarioDeLaSesion(pedidoConSesion(servidor))

    expect(usuario).toBeNull()
  })

  it('SES-4i: una respuesta sin email devuelve null', async () => {
    const servidor = crearServidorFalso()
    servidor.fallarRuta(RUTA, { cuerpo: { roles: ['odontologo'] } })

    const usuario = await obtenerUsuarioDeLaSesion(pedidoConSesion(servidor))

    expect(usuario).toBeNull()
  })

  it('SES-4f: una falla de red levanta SinConexion', async () => {
    const servidor = crearServidorFalso()
    servidor.fallarRuta(RUTA, 'red')

    const error = await obtenerUsuarioDeLaSesion(pedidoConSesion(servidor)).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(SinConexion)
  })

  it('SES-4g: un 500 levanta SinConexion', async () => {
    const servidor = crearServidorFalso()
    servidor.fallarRuta(RUTA, 500)

    const error = await obtenerUsuarioDeLaSesion(pedidoConSesion(servidor)).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(SinConexion)
    expect(servidor.llamadas('GET', RUTA)).toBe(1)
  })
})
