import { beforeEach, describe, expect, it } from 'vitest'
import {
  CONTRASENA_FICTICIA,
  EMAIL_ACTIVA,
  EMAIL_INACTIVA,
  crearServidorFalso,
} from '../../test/servidorFalso'
import { crearClienteHttp } from './clienteHttp'
import { CredencialesRechazadas, EntradaRechazada, SesionTerminada, SinConexion } from './errores'
import { CLAVE_DE_SESION, crearSesion } from './sesion'

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

describe('clienteHttp: iniciarSesion, bordes', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  function nuevo(servidor = crearServidorFalso(), almacenamiento?: Parameters<typeof crearSesion>[0]) {
    const sesion = almacenamiento === undefined ? crearSesion() : crearSesion(almacenamiento)
    return { servidor, sesion, cliente: crearClienteHttp({ fetch: servidor.fetch, sesion }) }
  }

  it('US-090 CA-2: 422 levanta EntradaRechazada', async () => {
    const { cliente, sesion } = nuevo()

    const error = await cliente.iniciarSesion('no-es-un-email', CONTRASENA_FICTICIA).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(EntradaRechazada)
    expect(sesion.access()).toBeNull()
  })

  it('US-090 CA-2: sin conexión o 5xx levanta SinConexion', async () => {
    const caido = nuevo()
    caido.servidor.caerse()
    const falla5xx = nuevo()
    falla5xx.servidor.responderConError(503)

    const sinRed = await caido.cliente.iniciarSesion(EMAIL_ACTIVA, CONTRASENA_FICTICIA).catch((e: unknown) => e)
    const con503 = await falla5xx.cliente.iniciarSesion(EMAIL_ACTIVA, CONTRASENA_FICTICIA).catch((e: unknown) => e)

    expect(sinRed).toBeInstanceOf(SinConexion)
    expect(con503).toBeInstanceOf(SinConexion)
    expect(caido.sesion.access()).toBeNull()
    expect(falla5xx.sesion.access()).toBeNull()
  })

  it('US-090 CA-2: un 401 del login no pide refresh aunque haya uno guardado', async () => {
    sessionStorage.setItem(CLAVE_DE_SESION, JSON.stringify({ refresh: 'refresco-guardado' }))
    const { cliente, servidor } = nuevo()

    const error = await cliente.iniciarSesion(EMAIL_ACTIVA, 'otra-clave-ficticia').catch((e: unknown) => e)

    expect(error).toBeInstanceOf(CredencialesRechazadas)
    expect(servidor.peticiones('/api/auth/refresh')).toBe(0)
    expect(servidor.peticiones('/api/auth/login')).toBe(1)
  })

  it('F7: sin sessionStorage disponible la sesión vive en memoria', async () => {
    const almacenamientoQueLanza = {
      getItem: () => null,
      setItem: () => {
        throw new DOMException('Almacenamiento bloqueado', 'SecurityError')
      },
      removeItem: () => {
        throw new DOMException('Almacenamiento bloqueado', 'SecurityError')
      },
    }
    const { cliente, sesion } = nuevo(crearServidorFalso(), almacenamientoQueLanza)

    await cliente.iniciarSesion(EMAIL_ACTIVA, CONTRASENA_FICTICIA)
    const accessGuardado = sesion.access()
    sesion.borrar()

    expect(accessGuardado).not.toBeNull()
    expect(sesion.refresh()).toBeNull()
  })
})

describe('clienteHttp: pedidoDelPanel', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  async function conSesion() {
    const servidor = crearServidorFalso()
    const sesion = crearSesion()
    const cliente = crearClienteHttp({ fetch: servidor.fetch, sesion })
    await cliente.iniciarSesion(EMAIL_ACTIVA, CONTRASENA_FICTICIA)
    return { servidor, sesion, cliente }
  }

  it('US-092 CA-1: pedidoDelPanel manda el Bearer del access', async () => {
    const { servidor, sesion } = await conSesion()
    let cabeceraEnviada: unknown = null
    const espia = crearClienteHttp({
      sesion,
      fetch: (entrada, init) => {
        cabeceraEnviada = init?.headers
        return servidor.fetch(entrada, init)
      },
    })

    const respuesta = await espia.pedidoDelPanel('/api/prestaciones')

    expect(respuesta.status).toBe(200)
    expect(cabeceraEnviada).toMatchObject({ Authorization: `Bearer ${sesion.access()}` })
    expect(servidor.peticiones('/api/auth/refresh')).toBe(0)
  })

  it('US-092 CA-1: access vencido se renueva una vez y repite la petición', async () => {
    const { servidor, sesion, cliente } = await conSesion()
    const accessViejo = sesion.access()
    servidor.vencerAccess()

    const respuesta = await cliente.pedidoDelPanel('/api/prestaciones')

    expect(respuesta.status).toBe(200)
    expect(servidor.peticiones('/api/auth/refresh')).toBe(1)
    expect(servidor.peticiones('/api/prestaciones')).toBe(2)
    expect(sesion.access()).not.toBe(accessViejo)
    expect(sesion.access()).not.toBeNull()
  })

  it('US-092 CA-1: refresh rechazado borra la sesión y levanta SesionTerminada', async () => {
    const { servidor, sesion, cliente } = await conSesion()
    servidor.vencerAccess()
    servidor.invalidarRefresh()

    const error = await cliente.pedidoDelPanel('/api/prestaciones').catch((e: unknown) => e)

    expect(error).toBeInstanceOf(SesionTerminada)
    expect((error as SesionTerminada).codigo).toBe('RN-AU-03')
    expect(sesion.access()).toBeNull()
    expect(sesion.refresh()).toBeNull()
    expect(sessionStorage.getItem(CLAVE_DE_SESION)).toBeNull()
  })

  it('US-092 CA-1: tres 401 simultáneos comparten una sola renovación', async () => {
    const { servidor, cliente } = await conSesion()
    servidor.vencerAccess()

    const respuestas = await Promise.all([
      cliente.pedidoDelPanel('/api/prestaciones'),
      cliente.pedidoDelPanel('/api/prestaciones'),
      cliente.pedidoDelPanel('/api/prestaciones'),
    ])

    expect(respuestas.map((r) => r.status)).toEqual([200, 200, 200])
    expect(servidor.peticiones('/api/auth/refresh')).toBe(1)
  })

  it('US-092 CA-1: la repetición con 401 no vuelve a renovar', async () => {
    const { servidor, sesion, cliente } = await conSesion()
    servidor.rechazarAccessSiempre()

    const error = await cliente.pedidoDelPanel('/api/prestaciones').catch((e: unknown) => e)

    expect(error).toBeInstanceOf(SesionTerminada)
    expect(servidor.peticiones('/api/auth/refresh')).toBe(1)
    expect(servidor.peticiones('/api/prestaciones')).toBe(2)
    expect(sesion.access()).toBeNull()
  })

  it('US-092 CA-1: sin refresh guardado un 401 levanta SesionTerminada sin pedir refresh', async () => {
    const servidor = crearServidorFalso()
    const sesion = crearSesion()
    sesion.guardarAccess('acceso-que-nadie-emitio')
    const cliente = crearClienteHttp({ fetch: servidor.fetch, sesion })

    const error = await cliente.pedidoDelPanel('/api/prestaciones').catch((e: unknown) => e)

    expect(error).toBeInstanceOf(SesionTerminada)
    expect(servidor.peticiones('/api/auth/refresh')).toBe(0)
    expect(sesion.access()).toBeNull()
  })

  it('US-092 CA-1: un 403 no renueva ni borra la sesión y devuelve RN-AU-05', async () => {
    const { servidor, sesion, cliente } = await conSesion()
    servidor.quitarPermiso(EMAIL_ACTIVA)

    const respuesta = await cliente.pedidoDelPanel('/api/prestaciones')
    const cuerpo: { codigos: string[] } = await respuesta.json()

    expect(respuesta.status).toBe(403)
    expect(cuerpo.codigos).toEqual(['RN-AU-05'])
    expect(servidor.peticiones('/api/auth/refresh')).toBe(0)
    expect(sesion.access()).not.toBeNull()
    expect(sesion.refresh()).not.toBeNull()
  })
})
