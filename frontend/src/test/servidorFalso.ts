// Servidor falso de la API del panel (design F13). Implementación alternativa escrita a mano de `fetch`,
// inyectada por parámetro: no es vi.mock. Las respuestas citan los contratos vigentes de
// `sesion-del-panel` (login, refresh) y `proteccion-del-panel` (rutas del panel). Todo es ficticio (RN-PR-01).

export type Fetch = (entrada: string, init?: RequestInit) => Promise<Response>

export const EMAIL_ACTIVA = 'odontologa@consultorio-demo.test'
export const EMAIL_INACTIVA = 'recepcion@consultorio-demo.test'
export const CONTRASENA_FICTICIA = 'clave-ficticia-de-prueba'

const TEXTO_CREDENCIALES = 'El email o la contraseña no son correctos.'

export interface ServidorFalso {
  fetch: Fetch
  /** Cantidad de peticiones recibidas por esa ruta (por ejemplo `/api/auth/login`). */
  peticiones(ruta: string): number
  /** A partir de ahora toda petición falla como una red caída (fetch rechaza). */
  caerse(): void
  /** A partir de ahora toda petición responde con ese estado 5xx. */
  responderConError(estado: number): void
}

function problema(estado: number, tipo: string, titulo: string, detalle: string, codigos: string[]): Response {
  const cuerpo = { type: tipo, title: titulo, status: estado, detail: detalle, codigos }
  return new Response(JSON.stringify(cuerpo), {
    status: estado,
    headers: { 'Content-Type': 'application/problem+json' },
  })
}

function json(estado: number, cuerpo: unknown): Response {
  return new Response(JSON.stringify(cuerpo), {
    status: estado,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  })
}

function leerCuerpo(init: RequestInit | undefined): Record<string, unknown> | null {
  if (typeof init?.body !== 'string') return null
  try {
    const valor: unknown = JSON.parse(init.body)
    return typeof valor === 'object' && valor !== null ? (valor as Record<string, unknown>) : null
  } catch {
    return null
  }
}

export function crearServidorFalso(): ServidorFalso {
  const contadores = new Map<string, number>()
  let caido = false
  let estado5xx: number | null = null
  let secuencia = 0

  function login(init: RequestInit | undefined): Response {
    const cuerpo = leerCuerpo(init)
    const email = cuerpo?.email
    const contrasena = cuerpo?.contrasena
    if (typeof email !== 'string' || !email.includes('@') || typeof contrasena !== 'string' || contrasena === '') {
      return problema(422, '/errores/entrada-invalida', 'Entrada inválida', 'La entrada no es válida.', [])
    }
    const activa = email.trim().toLowerCase() === EMAIL_ACTIVA && contrasena === CONTRASENA_FICTICIA
    if (!activa) {
      return problema(401, '/errores/credenciales-invalidas', 'Credenciales inválidas', TEXTO_CREDENCIALES, [
        'RN-AU-04',
      ])
    }
    secuencia += 1
    return json(200, {
      access_token: `acceso-${secuencia}`,
      refresh_token: `refresco-${secuencia}`,
      token_type: 'bearer',
      expires_in: 900,
    })
  }

  const falso: Fetch = (entrada, init) => {
    contadores.set(entrada, (contadores.get(entrada) ?? 0) + 1)
    if (caido) return Promise.reject(new TypeError('Failed to fetch'))
    if (estado5xx !== null) {
      return Promise.resolve(problema(estado5xx, '/errores/interno', 'Error del servidor', 'Error.', []))
    }
    if (entrada === '/api/auth/login' && init?.method === 'POST') return Promise.resolve(login(init))
    return Promise.resolve(problema(404, '/errores/recurso-no-encontrado', 'Recurso no encontrado', 'No existe.', []))
  }

  return {
    fetch: falso,
    peticiones: (ruta) => contadores.get(ruta) ?? 0,
    caerse: () => {
      caido = true
    },
    responderConError: (estado) => {
      estado5xx = estado
    },
  }
}
