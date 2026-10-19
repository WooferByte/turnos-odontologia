import { beforeEach, describe, expect, it } from 'vitest'
import {
  CONTRASENA_FICTICIA,
  EMAIL_ACTIVA,
  EMAIL_INACTIVA,
  crearServidorFalso,
} from '../../test/servidorFalso'
import { crearClienteHttp } from './clienteHttp'
import { CredencialesRechazadas } from './errores'
import { crearSesion } from './sesion'

const CLAVE_DE_SESION = 'turnos.sesion.v1'

describe('clienteHttp: iniciarSesion', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  it('US-090 CA-1: login válido devuelve y guarda los dos tokens', async () => {
    const servidor = crearServidorFalso()
    const sesion = crearSesion()
    const cliente = crearClienteHttp({ fetch: servidor.fetch, sesion })

    await cliente.iniciarSesion(EMAIL_ACTIVA, CONTRASENA_FICTICIA)

    expect(sesion.access()).not.toBeNull()
    expect(sesion.refresh()).not.toBeNull()
    expect(JSON.parse(sessionStorage.getItem(CLAVE_DE_SESION) ?? 'null')).toEqual({ refresh: sesion.refresh() })
    expect(servidor.peticiones('/api/auth/login')).toBe(1)
  })

  it('US-090 CA-1: el cuerpo enviado es solo email y contrasena', async () => {
    const servidor = crearServidorFalso()
    let cuerpoEnviado: unknown = null
    const espia = (entrada: string, init?: RequestInit) => {
      cuerpoEnviado = init?.body
      return servidor.fetch(entrada, init)
    }
    const cliente = crearClienteHttp({ fetch: espia, sesion: crearSesion() })

    await cliente.iniciarSesion(EMAIL_ACTIVA, CONTRASENA_FICTICIA)

    expect(JSON.parse(String(cuerpoEnviado))).toEqual({ email: EMAIL_ACTIVA, contrasena: CONTRASENA_FICTICIA })
  })

  async function intentar(email: string, contrasena: string) {
    const servidor = crearServidorFalso()
    const sesion = crearSesion()
    const cliente = crearClienteHttp({ fetch: servidor.fetch, sesion })
    const error = await cliente.iniciarSesion(email, contrasena).then(
      () => null,
      (e: unknown) => e,
    )
    return { error, sesion }
  }

  it('US-090 CA-2: email inexistente levanta CredencialesRechazadas con RN-AU-04', async () => {
    const { error, sesion } = await intentar('nadie@consultorio-demo.test', CONTRASENA_FICTICIA)

    expect(error).toBeInstanceOf(CredencialesRechazadas)
    expect((error as CredencialesRechazadas).codigo).toBe('RN-AU-04')
    expect(sesion.access()).toBeNull()
    expect(sesion.refresh()).toBeNull()
    expect(sessionStorage.getItem(CLAVE_DE_SESION)).toBeNull()
  })

  it('US-090 CA-2: contraseña incorrecta levanta lo mismo', async () => {
    const { error, sesion } = await intentar(EMAIL_ACTIVA, 'otra-clave-ficticia')

    expect(error).toBeInstanceOf(CredencialesRechazadas)
    expect((error as CredencialesRechazadas).codigo).toBe('RN-AU-04')
    expect(sesion.refresh()).toBeNull()
    expect(sessionStorage.getItem(CLAVE_DE_SESION)).toBeNull()
  })

  it('US-090 CA-3: usuaria inactiva levanta lo mismo', async () => {
    const { error, sesion } = await intentar(EMAIL_INACTIVA, CONTRASENA_FICTICIA)

    expect(error).toBeInstanceOf(CredencialesRechazadas)
    expect((error as CredencialesRechazadas).codigo).toBe('RN-AU-04')
    expect(sesion.access()).toBeNull()
    expect(sessionStorage.getItem(CLAVE_DE_SESION)).toBeNull()
  })
})
