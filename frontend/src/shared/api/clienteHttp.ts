// Cliente HTTP del panel (design F8, F12). Habla siempre con `/api` del mismo origen (F5) y recibe
// `fetch` inyectado: en producción el real, en los tests el servidor falso.
import { CredencialesRechazadas, SesionTerminada, SinConexion } from './errores'
import { traducirRechazo } from './rechazos'
import type { Sesion } from './sesion'

export type Fetch = (entrada: string, init?: RequestInit) => Promise<Response>

export interface OpcionesDelCliente {
  fetch?: Fetch
  sesion: Sesion
}

export interface ClienteHttp {
  iniciarSesion(email: string, contrasena: string): Promise<void>
  /**
   * Pedido a una ruta del panel con el Bearer del access. Un 401 renueva una vez y repite una vez;
   * un 403 (u otro 4xx) se devuelve al llamador sin tocar la sesión.
   */
  pedidoDelPanel(ruta: string, opciones?: RequestInit): Promise<Response>
  /** Renueva el access con el refresh guardado (arranque del panel). Comparte la renovación en curso. */
  renovarSesion(): Promise<void>
}

type Contexto = 'login' | 'refresh' | 'panel'

const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor.'
const MENSAJE_SESION_TERMINADA = 'La sesión terminó.'
const CODIGO_SESION_INVALIDA = 'RN-AU-03'

async function codigoDeRespuesta(respuesta: Response): Promise<string | null> {
  try {
    const cuerpo: unknown = await respuesta.clone().json()
    if (typeof cuerpo === 'object' && cuerpo !== null && 'codigos' in cuerpo && Array.isArray(cuerpo.codigos)) {
      const primero: unknown = cuerpo.codigos[0]
      return typeof primero === 'string' ? primero : null
    }
    return null
  } catch {
    return null
  }
}

/**
 * Única función que traduce una respuesta a un error (F12). Devuelve null cuando la respuesta no es un
 * error para ese contexto: un 2xx, o en el panel un 4xx que decide el llamador (401 renueva, 403 se devuelve).
 */
async function errorDeRespuesta(respuesta: Response, contexto: Contexto): Promise<Error | null> {
  if (respuesta.status >= 500) return new SinConexion(MENSAJE_SIN_CONEXION, null)
  if (respuesta.ok) return null
  if (contexto === 'login' && respuesta.status === 401) {
    return new CredencialesRechazadas('Credenciales rechazadas.', await codigoDeRespuesta(respuesta))
  }
  if (contexto === 'login' && respuesta.status === 422) {
    return traducirRechazo(respuesta)
  }
  if (contexto === 'refresh' && respuesta.status === 401) {
    return new SesionTerminada(MENSAJE_SESION_TERMINADA, CODIGO_SESION_INVALIDA)
  }
  if (contexto === 'panel') return null
  return new SinConexion(MENSAJE_SIN_CONEXION, null)
}

async function enviar(fetchInyectado: Fetch, entrada: string, init: RequestInit): Promise<Response> {
  try {
    return await fetchInyectado(entrada, init)
  } catch {
    throw new SinConexion(MENSAJE_SIN_CONEXION, null)
  }
}

async function leerCuerpo(respuesta: Response): Promise<Record<string, unknown>> {
  try {
    const cuerpo: unknown = await respuesta.json()
    if (typeof cuerpo === 'object' && cuerpo !== null) return cuerpo as Record<string, unknown>
  } catch {
    // Cuerpo ilegible: se trata como falla de transporte.
  }
  throw new SinConexion(MENSAJE_SIN_CONEXION, null)
}

export function crearClienteHttp(opciones: OpcionesDelCliente): ClienteHttp {
  const fetchInyectado: Fetch = opciones.fetch ?? ((entrada, init) => globalThis.fetch(entrada, init))
  const { sesion } = opciones
  let renovacionEnCurso: Promise<void> | null = null

  async function pedirJson(contexto: Contexto, ruta: string, cuerpo: unknown): Promise<Response> {
    const respuesta = await enviar(fetchInyectado, ruta, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cuerpo),
    })
    const error = await errorDeRespuesta(respuesta, contexto)
    if (error instanceof SesionTerminada) sesion.borrar()
    if (error !== null) throw error
    return respuesta
  }

  async function iniciarSesion(email: string, contrasena: string): Promise<void> {
    const respuesta = await pedirJson('login', '/api/auth/login', { email, contrasena })
    const cuerpo = await leerCuerpo(respuesta)
    if (typeof cuerpo.access_token !== 'string' || typeof cuerpo.refresh_token !== 'string') {
      throw new SinConexion(MENSAJE_SIN_CONEXION, null)
    }
    sesion.guardar(cuerpo.access_token, cuerpo.refresh_token)
  }

  async function renovar(): Promise<void> {
    const refresh = sesion.refresh()
    if (refresh === null) throw terminarSesion()
    const respuesta = await pedirJson('refresh', '/api/auth/refresh', { refresh_token: refresh })
    const cuerpo = await leerCuerpo(respuesta)
    if (typeof cuerpo.access_token !== 'string') throw new SinConexion(MENSAJE_SIN_CONEXION, null)
    sesion.guardarAccess(cuerpo.access_token)
  }

  function terminarSesion(): SesionTerminada {
    sesion.borrar()
    return new SesionTerminada(MENSAJE_SESION_TERMINADA, CODIGO_SESION_INVALIDA)
  }

  function renovarUnaVez(): Promise<void> {
    renovacionEnCurso ??= renovar().finally(() => {
      renovacionEnCurso = null
    })
    return renovacionEnCurso
  }

  async function enviarConAccess(ruta: string, opciones: RequestInit): Promise<Response> {
    const respuesta = await enviar(fetchInyectado, ruta, {
      ...opciones,
      headers: { ...opciones.headers, Authorization: `Bearer ${sesion.access() ?? ''}` },
    })
    const error = await errorDeRespuesta(respuesta, 'panel')
    if (error !== null) throw error
    return respuesta
  }

  async function pedidoDelPanel(ruta: string, opciones: RequestInit = {}): Promise<Response> {
    const primera = await enviarConAccess(ruta, opciones)
    if (primera.status !== 401) return primera
    await renovarUnaVez()
    const repetida = await enviarConAccess(ruta, opciones)
    if (repetida.status === 401) throw terminarSesion()
    return repetida
  }

  return { iniciarSesion, pedidoDelPanel, renovarSesion: renovarUnaVez }
}
