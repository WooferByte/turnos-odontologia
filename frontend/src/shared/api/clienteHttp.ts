// Cliente HTTP del panel (design F8, F12). Habla siempre con `/api` del mismo origen (F5) y recibe
// `fetch` inyectado: en producción el real, en los tests el servidor falso.
import { CredencialesRechazadas, EntradaRechazada, SesionTerminada, SinConexion } from './errores'
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

const MENSAJE_SESION_TERMINADA = 'La sesión terminó.'
const CODIGO_SESION_INVALIDA = 'RN-AU-03'

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

  async function enviarConAccess(ruta: string, opciones: RequestInit): Promise<Response> {
    const respuesta = await enviar(fetchInyectado, ruta, {
      ...opciones,
      headers: { ...opciones.headers, Authorization: `Bearer ${sesion.access() ?? ''}` },
    })
    if (respuesta.status >= 500) throw new SinConexion(MENSAJE_SIN_CONEXION, null)
    return respuesta
  }

  async function renovar(): Promise<void> {
    const refresh = sesion.refresh()
    if (refresh === null) throw terminarSesion()
    const respuesta = await enviar(fetchInyectado, '/api/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    })
    if (respuesta.status === 401) throw terminarSesion()
    if (respuesta.ok) {
      try {
        const cuerpo: unknown = await respuesta.json()
        if (typeof cuerpo === 'object' && cuerpo !== null && 'access_token' in cuerpo && typeof cuerpo.access_token === 'string') {
          sesion.guardarAccess(cuerpo.access_token)
          return
        }
      } catch {
        // Cuerpo ilegible: falla de transporte.
      }
    }
    throw new SinConexion(MENSAJE_SIN_CONEXION, null)
  }

  function terminarSesion(): SesionTerminada {
    sesion.borrar()
    return new SesionTerminada(MENSAJE_SESION_TERMINADA, CODIGO_SESION_INVALIDA)
  }

  let renovacionEnCurso: Promise<void> | null = null

  function renovarUnaVez(): Promise<void> {
    renovacionEnCurso ??= renovar().finally(() => {
      renovacionEnCurso = null
    })
    return renovacionEnCurso
  }

  async function pedidoDelPanel(ruta: string, opciones: RequestInit = {}): Promise<Response> {
    const primera = await enviarConAccess(ruta, opciones)
    if (primera.status !== 401) return primera
    await renovarUnaVez()
    const repetida = await enviarConAccess(ruta, opciones)
    if (repetida.status === 401) throw terminarSesion()
    return repetida
  }

  return { iniciarSesion, pedidoDelPanel }
}
