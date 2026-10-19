// Cliente HTTP del panel (design F8, F12). Habla siempre con `/api` del mismo origen (F5) y recibe
// `fetch` inyectado: en producción el real, en los tests el servidor falso.
import { CredencialesRechazadas, EntradaRechazada, SinConexion } from './errores'
import type { Sesion } from './sesion'

export type Fetch = (entrada: string, init?: RequestInit) => Promise<Response>

export interface OpcionesDelCliente {
  fetch?: Fetch
  sesion: Sesion
}

export interface ClienteHttp {
  iniciarSesion(email: string, contrasena: string): Promise<void>
}

const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor.'

async function codigoDeRespuesta(respuesta: Response): Promise<string | null> {
  try {
    const cuerpo: unknown = await respuesta.json()
    if (typeof cuerpo === 'object' && cuerpo !== null && 'codigos' in cuerpo && Array.isArray(cuerpo.codigos)) {
      const primero: unknown = cuerpo.codigos[0]
      return typeof primero === 'string' ? primero : null
    }
    return null
  } catch {
    return null
  }
}

/** Clasifica la respuesta del login (F12): devuelve el error que corresponde, o null si fue 200. */
async function errorDelLogin(respuesta: Response): Promise<Error | null> {
  if (respuesta.ok) return null
  if (respuesta.status === 401) {
    return new CredencialesRechazadas('Credenciales rechazadas.', await codigoDeRespuesta(respuesta))
  }
  if (respuesta.status === 422) {
    return new EntradaRechazada('Entrada rechazada.', await codigoDeRespuesta(respuesta))
  }
  return new SinConexion(MENSAJE_SIN_CONEXION, null)
}

async function enviar(fetchInyectado: Fetch, entrada: string, init: RequestInit): Promise<Response> {
  try {
    return await fetchInyectado(entrada, init)
  } catch {
    throw new SinConexion(MENSAJE_SIN_CONEXION, null)
  }
}

export function crearClienteHttp(opciones: OpcionesDelCliente): ClienteHttp {
  const fetchInyectado: Fetch = opciones.fetch ?? ((entrada, init) => globalThis.fetch(entrada, init))
  const { sesion } = opciones

  async function iniciarSesion(email: string, contrasena: string): Promise<void> {
    const respuesta = await enviar(fetchInyectado, '/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, contrasena }),
    })
    const error = await errorDelLogin(respuesta)
    if (error !== null) throw error
    try {
      const cuerpo: unknown = await respuesta.json()
      if (
        typeof cuerpo === 'object' &&
        cuerpo !== null &&
        'access_token' in cuerpo &&
        typeof cuerpo.access_token === 'string' &&
        'refresh_token' in cuerpo &&
        typeof cuerpo.refresh_token === 'string'
      ) {
        sesion.guardar(cuerpo.access_token, cuerpo.refresh_token)
        return
      }
    } catch {
      // Cuerpo ilegible: se trata como falla de transporte.
    }
    throw new SinConexion(MENSAJE_SIN_CONEXION, null)
  }

  return { iniciarSesion }
}
