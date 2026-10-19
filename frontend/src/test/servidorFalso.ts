// Servidor falso de la API del panel (design F13). Implementación alternativa escrita a mano de `fetch`,
// inyectada por parámetro: no es un mock de módulos. Las respuestas citan los contratos vigentes de
// `sesion-del-panel` (login, refresh) y `proteccion-del-panel` (rutas del panel). Todo es ficticio (RN-PR-01).

export type Fetch = (entrada: string, init?: RequestInit) => Promise<Response>

export const EMAIL_ACTIVA = 'odontologa@consultorio-demo.test'
export const EMAIL_INACTIVA = 'recepcion@consultorio-demo.test'
/**
 * La recepcionista de la demo. En el login del falso sigue inactiva (US-090 CA-3 de C-08); los tests de
 * las pantallas la usan con una sesión emitida (`emitirSesion(EMAIL_RECEPCIONISTA)`), con rol `recepcionista`.
 */
export const EMAIL_RECEPCIONISTA = EMAIL_INACTIVA
export const CONTRASENA_FICTICIA = 'clave-ficticia-de-prueba'

const TEXTO_CREDENCIALES = 'El email o la contraseña no son correctos.'
const TEXTO_SESION = 'La sesión no es válida o venció. Iniciá sesión de nuevo.'
const TEXTO_PERMISO = 'No tenés permiso para esta acción.'

export interface PrestacionFalsa {
  id: number
  nombre: string
  duracion_minutos: number
  color: string
  reservable_online: boolean
  activa: boolean
}

/** Las cinco prestaciones de la demo (ids 1 a 5); «Urgencia» está inactiva para los escenarios de la suite. */
export const PRESTACIONES_DE_PARTIDA: readonly PrestacionFalsa[] = [
  { id: 1, nombre: 'Consulta / control', duracion_minutos: 30, color: '#1E88E5', reservable_online: false, activa: true },
  { id: 2, nombre: 'Limpieza', duracion_minutos: 45, color: '#43A047', reservable_online: false, activa: true },
  { id: 3, nombre: 'Obturación', duracion_minutos: 60, color: '#FB8C00', reservable_online: false, activa: true },
  { id: 4, nombre: 'Extracción', duracion_minutos: 45, color: '#E53935', reservable_online: false, activa: true },
  { id: 5, nombre: 'Urgencia', duracion_minutos: 30, color: '#8E24AA', reservable_online: false, activa: false },
]

export interface OpcionesDelServidorFalso {
  /** Catálogo inicial de prestaciones; por defecto vacío. */
  prestaciones?: readonly PrestacionFalsa[]
}

export interface ServidorFalso {
  fetch: Fetch
  /** Cantidad de peticiones recibidas por esa ruta (por ejemplo `/api/auth/login`), de cualquier método. */
  peticiones(ruta: string): number
  /** Cantidad de peticiones de ese método a esa ruta. */
  llamadas(metodo: string, ruta: string): number
  /** Rutas pedidas hasta ahora, sin repetir y en orden de primera aparición. */
  rutasPedidas(): string[]
  /** Cuerpos JSON recibidos por ese método y esa ruta, en orden. */
  cuerpos(metodo: string, ruta: string): Record<string, unknown>[]
  /** Copia del catálogo del falso en este momento (para comprobar que algo no se creó). */
  catalogoActual(): PrestacionFalsa[]
  /** Saca una prestación del catálogo (la API no borra, RN-GL-03; sirve para simular una base recreada). */
  quitarPrestacion(id: number): void
  /** A partir de ahora toda petición falla como una red caída (fetch rechaza). */
  caerse(): void
  /** Deshace `caerse` y `responderConError`: la API vuelve a responder. */
  recuperar(): void
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

interface ErrorDeCampoFalso {
  campo: string | null
  codigo: string | null
  mensaje: string
}

interface ExtrasDelProblema {
  errores?: ErrorDeCampoFalso[]
  referencias?: { recurso: string; recurso_id: number; motivo: string }[]
}

function problema(
  estado: number,
  tipo: string,
  titulo: string,
  detalle: string,
  codigos: string[],
  extras: ExtrasDelProblema = {},
): Response {
  const cuerpo = { type: tipo, title: titulo, status: estado, detail: detalle, codigos, ...extras }
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

const ROLES: Record<string, readonly string[]> = {
  [EMAIL_ACTIVA]: ['odontologo', 'dueno'],
  [EMAIL_RECEPCIONISTA]: ['recepcionista'],
}
const COLOR_HEX = /^#[0-9A-Fa-f]{6}$/
const CAMPOS_DEL_ALTA = new Set(['nombre', 'duracion_minutos', 'color', 'reservable_online'])
const CAMPOS_DEL_PATCH = new Set(['nombre', 'duracion_minutos', 'color', 'reservable_online', 'activa'])
const MENSAJE_RN_AG_01 = "El campo 'duracion_minutos' debe ser mayor que 0 y múltiplo de 5 minutos."

function normalizarEspacios(texto: string): string {
  return texto.trim().replace(/\s+/g, ' ')
}

/** Clave de unicidad de RN-AG-15: sin mayúsculas, acentos ni espacios de más. */
function claveDeNombre(nombre: string): string {
  return normalizarEspacios(nombre).normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase()
}

function errorDeFormato(campo: string, mensaje: string): ErrorDeCampoFalso {
  return { campo, codigo: null, mensaje }
}

/** Errores de formato del cuerpo (422 sin código): lo que valida Pydantic antes que el dominio. */
function erroresDeFormato(cuerpo: Record<string, unknown> | null, permitidos: Set<string>, esAlta: boolean) {
  if (cuerpo === null) return [errorDeFormato('cuerpo', 'El cuerpo debe ser un objeto JSON.')]
  const errores: ErrorDeCampoFalso[] = []
  for (const campo of Object.keys(cuerpo)) {
    if (!permitidos.has(campo)) errores.push(errorDeFormato(campo, 'Campo no permitido.'))
  }
  if (esAlta) {
    for (const campo of ['nombre', 'duracion_minutos', 'color']) {
      if (!(campo in cuerpo)) errores.push(errorDeFormato(campo, 'Campo obligatorio.'))
    }
  }
  const { nombre, duracion_minutos: duracion, color, reservable_online: reservable, activa } = cuerpo
  if (nombre !== undefined && (typeof nombre !== 'string' || normalizarEspacios(nombre) === '')) {
    errores.push(errorDeFormato('nombre', 'El nombre no puede estar vacío.'))
  }
  if (duracion !== undefined && !Number.isInteger(duracion)) {
    errores.push(errorDeFormato('duracion_minutos', 'Debe ser un número entero.'))
  }
  if (color !== undefined && (typeof color !== 'string' || !COLOR_HEX.test(color))) {
    errores.push(errorDeFormato('color', 'Debe ser un color #RRGGBB.'))
  }
  if (reservable !== undefined && typeof reservable !== 'boolean') {
    errores.push(errorDeFormato('reservable_online', 'Debe ser verdadero o falso.'))
  }
  if (activa !== undefined && typeof activa !== 'boolean') {
    errores.push(errorDeFormato('activa', 'Debe ser verdadero o falso.'))
  }
  return errores
}

function duracionInvalida(duracion: unknown): boolean {
  return typeof duracion === 'number' && (duracion <= 0 || duracion % 5 !== 0)
}

export function crearServidorFalso(opciones: OpcionesDelServidorFalso = {}): ServidorFalso {
  const catalogo: PrestacionFalsa[] = (opciones.prestaciones ?? []).map((prestacion) => ({ ...prestacion }))
  const cuerposRecibidos = new Map<string, Record<string, unknown>[]>()
  const llamadasPorMetodo = new Map<string, number>()
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

  /** Autenticación y permiso (D208: antes que la validación). Devuelve el rechazo, o null si pasa. */
  function autorizar(init: RequestInit | undefined, escribe: boolean): Response | null {
    const token = bearer(init)
    const email = token === null ? undefined : accesos.get(token)
    if (email === undefined || accessSiempreRechazado) return sesionInvalida()
    const roles = ROLES[email] ?? []
    if (sinPermiso.has(email) || (escribe && !roles.includes('odontologo'))) {
      return problema(403, '/errores/permiso-insuficiente', 'Permiso insuficiente', TEXTO_PERMISO, ['RN-AU-05'])
    }
    return null
  }

  function entradaInvalida(errores: ErrorDeCampoFalso[], codigos: string[]): Response {
    return problema(422, '/errores/entrada-invalida', 'Entrada inválida', 'La entrada no es válida.', codigos, {
      errores,
    })
  }

  function nombreRepetido(nombre: string, excepto: number | null): boolean {
    const clave = claveDeNombre(nombre)
    return catalogo.some((p) => p.id !== excepto && claveDeNombre(p.nombre) === clave)
  }

  function rechazoRnAg01(): Response {
    return entradaInvalida(
      [{ campo: 'duracion_minutos', codigo: 'RN-AG-01', mensaje: MENSAJE_RN_AG_01 }],
      ['RN-AG-01'],
    )
  }

  function conflictoDeNombre(nombre: string): Response {
    return problema(409, '/errores/nombre-repetido', 'Nombre repetido', `Ya existe una prestación llamada «${nombre}».`, [
      'RN-AG-15',
    ])
  }

  function listarPrestaciones(init: RequestInit | undefined): Response {
    return autorizar(init, false) ?? json(200, catalogo.map((p) => ({ ...p })))
  }

  function crearPrestacion(init: RequestInit | undefined): Response {
    const rechazo = autorizar(init, true)
    if (rechazo !== null) return rechazo
    const cuerpo = leerCuerpo(init)
    const errores = erroresDeFormato(cuerpo, CAMPOS_DEL_ALTA, true)
    if (cuerpo === null || errores.length > 0) return entradaInvalida(errores, [])
    if (duracionInvalida(cuerpo.duracion_minutos)) return rechazoRnAg01()
    const nombre = normalizarEspacios(String(cuerpo.nombre))
    if (nombreRepetido(nombre, null)) return conflictoDeNombre(nombre)
    const nueva: PrestacionFalsa = {
      id: Math.max(0, ...catalogo.map((p) => p.id)) + 1,
      nombre,
      duracion_minutos: Number(cuerpo.duracion_minutos),
      color: String(cuerpo.color),
      reservable_online: cuerpo.reservable_online === true,
      activa: true,
    }
    catalogo.push(nueva)
    return json(201, { ...nueva })
  }

  function editarPrestacion(id: number, init: RequestInit | undefined): Response {
    const rechazo = autorizar(init, true)
    if (rechazo !== null) return rechazo
    const cuerpo = leerCuerpo(init)
    const errores = erroresDeFormato(cuerpo, CAMPOS_DEL_PATCH, false)
    if (cuerpo === null || errores.length > 0) return entradaInvalida(errores, [])
    const actual = catalogo.find((p) => p.id === id)
    if (actual === undefined) {
      return problema(404, '/errores/recurso-no-encontrado', 'Recurso no encontrado', 'No existe.', ['RN-GL-04'], {
        referencias: [{ recurso: 'prestacion', recurso_id: id, motivo: 'inexistente' }],
      })
    }
    if (duracionInvalida(cuerpo.duracion_minutos)) return rechazoRnAg01()
    const nombre = typeof cuerpo.nombre === 'string' ? normalizarEspacios(cuerpo.nombre) : null
    if (nombre !== null && nombreRepetido(nombre, id)) return conflictoDeNombre(nombre)
    if (nombre !== null) actual.nombre = nombre
    if (typeof cuerpo.duracion_minutos === 'number') actual.duracion_minutos = cuerpo.duracion_minutos
    if (typeof cuerpo.color === 'string') actual.color = cuerpo.color
    if (typeof cuerpo.reservable_online === 'boolean') actual.reservable_online = cuerpo.reservable_online
    if (typeof cuerpo.activa === 'boolean') actual.activa = cuerpo.activa
    return json(200, { ...actual })
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
    const metodo = init?.method ?? 'GET'
    const clave = `${metodo} ${entrada}`
    llamadasPorMetodo.set(clave, (llamadasPorMetodo.get(clave) ?? 0) + 1)
    const recibido = leerCuerpo(init)
    if (recibido !== null) cuerposRecibidos.set(clave, [...(cuerposRecibidos.get(clave) ?? []), recibido])
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
    const metodo = init?.method ?? 'GET'
    if (entrada === '/api/prestaciones' && metodo === 'GET') return Promise.resolve(listarPrestaciones(init))
    if (entrada === '/api/prestaciones' && metodo === 'POST') return Promise.resolve(crearPrestacion(init))
    const delPatch = /^\/api\/prestaciones\/(\d+)$/.exec(entrada)
    if (delPatch !== null && metodo === 'PATCH') {
      return Promise.resolve(editarPrestacion(Number(delPatch[1]), init))
    }
    return Promise.resolve(problema(404, '/errores/recurso-no-encontrado', 'Recurso no encontrado', 'No existe.', []))
  }

  return {
    fetch: falso,
    peticiones: (ruta) => contadores.get(ruta) ?? 0,
    rutasPedidas: () => [...contadores.keys()],
    llamadas: (metodo, ruta) => llamadasPorMetodo.get(`${metodo} ${ruta}`) ?? 0,
    cuerpos: (metodo, ruta) => cuerposRecibidos.get(`${metodo} ${ruta}`) ?? [],
    catalogoActual: () => catalogo.map((p) => ({ ...p })),
    quitarPrestacion: (id) => {
      const indice = catalogo.findIndex((p) => p.id === id)
      if (indice >= 0) catalogo.splice(indice, 1)
    },
    caerse: () => {
      caido = true
    },
    recuperar: () => {
      caido = false
      estado5xx = null
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
