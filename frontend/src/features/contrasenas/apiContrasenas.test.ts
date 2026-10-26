import { describe, expect, it } from 'vitest'
import { crearClienteHttp } from '../../shared/api/clienteHttp'
import { EntradaRechazada, PermisoInsuficiente, RecursoInexistente, ReglaRechazada } from '../../shared/api/errores'
import { crearSesion } from '../../shared/api/sesion'
import {
  CONTRASENA_DEMO,
  EMAIL_ACTIVA,
  EMAIL_DUENO,
  EMAIL_RECEPCIONISTA,
  USUARIOS_DE_PARTIDA,
  USUARIO_DUENO,
  crearServidorFalso,
  type ServidorFalso,
} from '../../test/servidorFalso'
import { crearApiContrasenas } from './apiContrasenas'

const NUEVA = 'clave-nueva-2026'

function apiConSesion(servidor: ServidorFalso, email: string = EMAIL_ACTIVA) {
  const sesion = crearSesion(null)
  const { access, refresh } = servidor.emitirSesion(email)
  sesion.guardar(access, refresh)
  const cliente = crearClienteHttp({ fetch: servidor.fetch, sesion })
  return crearApiContrasenas(cliente.pedidoDelPanel)
}

describe('apiContrasenas', () => {
  it('US-093 CA-6: restablecer responde sin cuerpo', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor)

    const resultado = await api.restablecerContrasena(2, NUEVA)

    expect(resultado).toBeUndefined()
    expect(servidor.cuerpos('POST', '/api/usuarios/2/restablecer-contrasena')).toEqual([{ contrasena: NUEVA }])
    expect(servidor.contrasenaDe(EMAIL_RECEPCIONISTA)).toBe(NUEVA)
  })

  it('US-093 CA-6: la odontóloga sobre su propia fila levanta ReglaRechazada con RN-AU-10', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor)

    const error = await api.restablecerContrasena(1, NUEVA).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ReglaRechazada)
    expect((error as ReglaRechazada).codigo).toBe('RN-AU-10')
    expect(servidor.contrasenaDe(EMAIL_ACTIVA)).not.toBe(NUEVA)
  })

  it('US-093 CA-6: el dueño que restablece recibe PermisoInsuficiente', async () => {
    const servidor = crearServidorFalso({ usuarios: [...USUARIOS_DE_PARTIDA, USUARIO_DUENO] })
    const api = apiConSesion(servidor, EMAIL_DUENO)

    const error = await api.restablecerContrasena(2, NUEVA).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(PermisoInsuficiente)
    expect((error as PermisoInsuficiente).codigo).toBe('RN-AU-05')
    expect(servidor.contrasenaDe(EMAIL_RECEPCIONISTA)).toBe(CONTRASENA_DEMO)
  })

  it('US-093 CA-6: un usuario inexistente levanta RecursoInexistente con RN-GL-04', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor)

    const error = await api.restablecerContrasena(999, NUEVA).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(RecursoInexistente)
    expect((error as RecursoInexistente).codigo).toBe('RN-GL-04')
  })

  it('US-093 CA-9: la nueva corta levanta EntradaRechazada con el error de contrasena_nueva', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor, EMAIL_RECEPCIONISTA)

    const error = await api.cambiarContrasena(CONTRASENA_DEMO, 'corta-123').catch((e: unknown) => e)

    expect(error).toBeInstanceOf(EntradaRechazada)
    const rechazo = error as EntradaRechazada
    expect(rechazo.codigos).toEqual(['RN-AU-07'])
    expect(rechazo.errores.map((e) => e.campo)).toEqual(['contrasena_nueva'])
    expect(servidor.contrasenaDe(EMAIL_RECEPCIONISTA)).toBe(CONTRASENA_DEMO)
  })

  it('US-093 CA-7: cambiar devuelve los tokens nuevos', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor, EMAIL_RECEPCIONISTA)

    const tokens = await api.cambiarContrasena(CONTRASENA_DEMO, NUEVA)

    expect(tokens.access).not.toBe('')
    expect(tokens.refresh).not.toBe('')
    expect(servidor.cuerpos('POST', '/api/auth/cambiar-contrasena')).toEqual([
      { contrasena_actual: CONTRASENA_DEMO, contrasena_nueva: NUEVA },
    ])
    expect(servidor.contrasenaDe(EMAIL_RECEPCIONISTA)).toBe(NUEVA)
  })

  it('US-093 CA-7: la actual incorrecta levanta EntradaRechazada con RN-AU-09', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor, EMAIL_RECEPCIONISTA)

    const error = await api.cambiarContrasena('no-es-la-actual-2026', NUEVA).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(EntradaRechazada)
    expect((error as EntradaRechazada).codigo).toBe('RN-AU-09')
    expect(servidor.contrasenaDe(EMAIL_RECEPCIONISTA)).toBe(CONTRASENA_DEMO)
  })
})
