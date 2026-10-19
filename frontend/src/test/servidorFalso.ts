// Servidor falso de la API del panel (design F13). Implementación alternativa escrita a mano de `fetch`,
// inyectada por parámetro: no es vi.mock. Las respuestas citan los contratos vigentes de
// `sesion-del-panel` (login, refresh) y `proteccion-del-panel` (rutas del panel). Todo es ficticio (RN-PR-01).

export type Fetch = (entrada: string, init?: RequestInit) => Promise<Response>

export const EMAIL_ACTIVA = 'odontologa@consultorio-demo.test'
export const EMAIL_INACTIVA = 'recepcion@consultorio-demo.test'
export const CONTRASENA_FICTICIA = 'clave-ficticia-de-prueba'

const TEXTO_CREDENCIALES = 'El email o la contraseña no son correctos.'
const TEXTO_SESION = 'La sesión no es válida o venció. Iniciá sesión de nuevo.'
const TEXTO_PERMISO = 'No tenés permiso para esta acción.'

export interface ServidorFalso {
  fetch: Fetch
  /** Cantidad de peticiones recibidas por esa ruta (por ejemplo `/api/auth/login`). */
  peticiones(ruta: string): number
  /** A partir de ahora toda petición falla como una red caída (fetch rechaza). */
  caerse(): void
  /** A partir de ahora toda petición responde con ese estado 5xx. */
  responderConError(estado: number): void
  /** Todos los access emitidos hasta ahora pasan a vencidos (401 RN-AU-03); el refresh sigue válido. */
  vencerAccess(): void
  /** Todos los refresh emitidos hasta ahora pasan a inválidos (el refresh responde 401 RN-AU-03). */
  invalidarRefresh(): void
  /** El usuario deja de tener permiso en las rutas del panel (403 RN-AU-05). */
  quitarPermiso(email: string): void
  /** Las rutas del panel responden 401 RN-AU-03 aunque el access sea válido (para probar que no hay bucles). */
  rechazarAccessSiempre(): void
  /** Las peticiones a esa ruta quedan esperando hasta que se llame a la función devuelta. */
  retener(ruta: string): () => void
  /** Emite una sesión válida sin pasar por el login (por ejemplo, para simular un refresh ya guardado). */
  emitirSesion(email?: string): { access: string; refresh: string }
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
  const accesos = new Map<string, string>()
  const refrescos = new Map<string, string>()
  const sinPermiso = new Set<string>()
  let accessSiempreRechazado = false
  const retenciones = new Map<string, Promise<void>>()

  function emitirAccess(email: string): string {
    secuencia += 1
    const token = `acceso-${secuencia}`
    accesos.set(token, email)
    return token
  }

  function sesionInvalida(): Response {
    return problema(401, '/errores/sesion-invalida', 'Sesión inválida', TEXTO_SESION, ['RN-AU-03'])
  }

  function bearer(init: RequestInit | undefined): string | null {
    const cabeceras = init?.headers
    const valor = cabeceras !== undefined && !Array.isArray(cabeceras) && !(cabeceras instanceof Headers)
      ? cabeceras['Authorization']
      : undefined
    return typeof valor === 'string' && valor.startsWith('Bearer ') ? valor.slice('Bearer '.length) : null
  }

  function prestaciones(init: RequestInit | undefined): Response {
    const token = bearer(init)
    const email = token === null ? undefined : accesos.get(token)
    if (email === undefined || accessSiempreRechazado) return sesionInvalida()
    if (sinPermiso.has(email)) {
      return problema(403, '/errores/permiso-insuficiente', 'Permiso insuficiente', TEXTO_PERMISO, ['RN-AU-05'])
    }
    return json(200, [])
  }

  async function refrescar(init: RequestInit | undefined): Promise<Response> {
    // Una vuelta del bucle de eventos: da tiempo a que lleguen varios 401 antes de contestar.
    await new Promise<void>((resolver) => setTimeout(resolver, 0))
    const token = leerCuerpo(init)?.refresh_token
    const email = typeof token === 'string' ? refrescos.get(token) : undefined
    if (email === undefined) return sesionInvalida()
    return json(200, { access_token: emitirAccess(email), token_type: 'bearer', expires_in: 900 })
  }

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
    const accessToken = emitirAccess(EMAIL_ACTIVA)
    const refreshToken = `refresco-${secuencia}`
    refrescos.set(refreshToken, EMAIL_ACTIVA)
    return json(200, {
      access_token: accessToken,
      refresh_token: refreshToken,
      token_type: 'bearer',
      expires_in: 900,
    })
  }

  const falso: Fetch = (entrada, init) => {
    contadores.set(entrada, (contadores.get(entrada) ?? 0) + 1)
    const retencion = retenciones.get(entrada)
    return retencion === undefined ? despachar(entrada, init) : retencion.then(() => despachar(entrada, init))
  }

  function despachar(entrada: string, init: RequestInit | undefined): Promise<Response> {
    if (caido) return Promise.reject(new TypeError('Failed to fetch'))
    if (estado5xx !== null) {
      return Promise.resolve(problema(estado5xx, '/errores/interno', 'Error del servidor', 'Error.', []))
    }
    if (entrada === '/api/auth/login' && init?.method === 'POST') return Promise.resolve(login(init))
    if (entrada === '/api/auth/refresh' && init?.method === 'POST') return refrescar(init)
    if (entrada === '/api/prestaciones' && (init?.method ?? 'GET') === 'GET') {
      return Promise.resolve(prestaciones(init))
    }
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
    vencerAccess: () => {
      accesos.clear()
    },
    invalidarRefresh: () => {
      refrescos.clear()
    },
    quitarPermiso: (email) => {
      sinPermiso.add(email)
    },
    rechazarAccessSiempre: () => {
      accessSiempreRechazado = true
    },
    retener: (ruta) => {
      let liberar: () => void = () => undefined
      retenciones.set(
        ruta,
        new Promise<void>((resolver) => {
          liberar = resolver
        }),
      )
      return liberar
    },
    emitirSesion: (email = EMAIL_ACTIVA) => {
      const access = emitirAccess(email)
      const refresh = `refresco-${secuencia}`
      refrescos.set(refresh, email)
      return { access, refresh }
    },
  }
}
