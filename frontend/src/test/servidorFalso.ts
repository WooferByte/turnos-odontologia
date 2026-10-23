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

export interface UsuarioFalso {
  id: number
  email: string
  roles: string[]
  activo: boolean
}

export const EMAIL_DUENO = 'dueno@consultorio-demo.test'
export const EMAIL_ADMINISTRACION = 'administracion@consultorio-demo.test'

/**
 * Los usuarios de la API real (design U21): la odontóloga, la recepcionista y `administracion`, inactivo y solo
 * `dueno`. De este catálogo salen los roles de cada sesión. La recepcionista figura activa porque es lo que
 * devuelve la API; en el login del falso sigue inactiva (C-08), ver `EMAIL_RECEPCIONISTA`.
 */
export const USUARIOS_DE_PARTIDA: readonly UsuarioFalso[] = [
  { id: 1, email: EMAIL_ACTIVA, roles: ['odontologo', 'dueno'], activo: true },
  { id: 2, email: EMAIL_RECEPCIONISTA, roles: ['recepcionista'], activo: true },
  { id: 3, email: EMAIL_ADMINISTRACION, roles: ['dueno'], activo: false },
]

/** Un usuario solo `dueno` y activo, que el catálogo de partida no trae (H12). */
export const USUARIO_DUENO: UsuarioFalso = { id: 4, email: EMAIL_DUENO, roles: ['dueno'], activo: true }

export interface ProfesionalFalso {
  id: number
  nombre: string
  activo: boolean
}

export interface FranjaFalsa {
  dia_semana: number
  hora_inicio: string
  hora_fin: string
}

export const ZONA_DEL_CONSULTORIO = 'America/Argentina/Buenos_Aires'

/** El profesional de la demo (id 1), activo. */
export const PROFESIONALES_DE_PARTIDA: readonly ProfesionalFalso[] = [
  { id: 1, nombre: 'Dra. Demo Ficticia', activo: true },
]

/** Un segundo profesional, inactivo y sin franjas, para los escenarios del selector. */
export const PROFESIONAL_INACTIVO: ProfesionalFalso = { id: 2, nombre: 'Dr. Ejemplo Ficticio', activo: false }

/** El horario de la demo: lunes a viernes 09:00-13:00 y 15:00-19:00 (diez franjas, D56). */
export const HORARIO_DE_LA_DEMO: readonly FranjaFalsa[] = [0, 1, 2, 3, 4].flatMap((dia) => [
  { dia_semana: dia, hora_inicio: '09:00', hora_fin: '13:00' },
  { dia_semana: dia, hora_inicio: '15:00', hora_fin: '19:00' },
])

export interface OpcionesDelServidorFalso {
  /** Profesionales del consultorio; por defecto `PROFESIONALES_DE_PARTIDA`. */
  profesionales?: readonly ProfesionalFalso[]
  /** Horario de cada profesional por id; el profesional 1 parte con `HORARIO_DE_LA_DEMO` y los demás sin franjas. */
  horarios?: Readonly<Record<number, readonly FranjaFalsa[]>>
  /** Catálogo inicial de prestaciones; por defecto vacío. */
  prestaciones?: readonly PrestacionFalsa[]
  /** Usuarios del consultorio; por defecto `USUARIOS_DE_PARTIDA`. */
  usuarios?: readonly UsuarioFalso[]
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
  /** Copia de los usuarios del falso en este momento. */
  usuariosActuales(): UsuarioFalso[]
  /** Saca un usuario del catálogo (la API real no borra usuarios; sirve para simular un `404`). */
  quitarUsuario(id: number): void
  /** Saca una prestación del catálogo (la API no borra, RN-GL-03; sirve para simular una base recreada). */
  quitarPrestacion(id: number): void
  /** Copia del horario del falso para ese profesional (para comprobar que algo no se guardó). */
  horarioActual(profesionalId: number): FranjaFalsa[]
  /** Saca un profesional (la API real no borra profesionales, D46; sirve para simular un `404`). */
  quitarProfesional(id: number): void
  /** Marca inactivo a un profesional (la demo no tiene cómo hacerlo). */
  marcarInactivo(id: number): void
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

const ORDEN_DE_ROLES = ['odontologo', 'recepcionista', 'dueno']
const CAMPOS_DEL_ALTA_DE_USUARIO = new Set(['email', 'contrasena', 'roles'])
const CAMPOS_DEL_PATCH_DE_USUARIO = new Set(['roles', 'activo'])
const FORMATO_DE_EMAIL = /^[^@\s]+@[^@\s]+$/
const MENSAJE_RN_AU_07 = 'La contraseña debe tener de 10 caracteres a 72 bytes.'
const DETALLE_DESACTIVARSE = 'Nadie puede desactivarse a sí mismo.'
const DETALLE_SIN_ODONTOLOGO = 'El consultorio no puede quedar sin un odontólogo activo.'
const COLOR_HEX = /^#[0-9A-Fa-f]{6}$/
const CAMPOS_DEL_ALTA = new Set(['nombre', 'duracion_minutos', 'color', 'reservable_online'])
const CAMPOS_DEL_PATCH = new Set(['nombre', 'duracion_minutos', 'color', 'reservable_online', 'activa'])
const MENSAJE_RN_AG_01 = "El campo 'duracion_minutos' debe ser mayor que 0 y múltiplo de 5 minutos."

const HORA_DEL_DIA = /^([01]\d|2[0-3]):[0-5]\d$/
const CAMPOS_DE_FRANJA = new Set(['dia_semana', 'hora_inicio', 'hora_fin'])
const MAXIMO_DE_FRANJAS = 70

/** Errores de formato del `PUT` del horario (lo que valida Pydantic): campos de más, día, hora y el tope de 70. */
function erroresDeFormatoDeHorario(cuerpo: Record<string, unknown> | null): ErrorDeCampoFalso[] {
  if (cuerpo === null) return [errorDeFormato('cuerpo', 'El cuerpo debe ser un objeto JSON.')]
  const errores: ErrorDeCampoFalso[] = []
  for (const campo of Object.keys(cuerpo)) {
    if (campo !== 'franjas') errores.push(errorDeFormato(campo, 'Campo no permitido.'))
  }
  const franjas = cuerpo.franjas
  if (!Array.isArray(franjas)) return [...errores, errorDeFormato('franjas', 'Debe ser una lista.')]
  if (franjas.length > MAXIMO_DE_FRANJAS) errores.push(errorDeFormato('franjas', 'Hay más de 70 franjas.'))
  franjas.forEach((franja: unknown, i) => {
    if (typeof franja !== 'object' || franja === null) {
      errores.push(errorDeFormato(`franjas.${i}`, 'Debe ser un objeto.'))
      return
    }
    const f = franja as Record<string, unknown>
    for (const campo of Object.keys(f)) {
      if (!CAMPOS_DE_FRANJA.has(campo)) errores.push(errorDeFormato(`franjas.${i}.${campo}`, 'Campo no permitido.'))
    }
    const dia = f.dia_semana
    if (typeof dia !== 'number' || !Number.isInteger(dia) || dia < 0 || dia > 6) {
      errores.push(errorDeFormato(`franjas.${i}.dia_semana`, 'Debe ser un entero de 0 a 6.'))
    }
    for (const campo of ['hora_inicio', 'hora_fin']) {
      const hora = f[campo]
      if (typeof hora !== 'string' || !HORA_DEL_DIA.test(hora)) {
        errores.push(errorDeFormato(`franjas.${i}.${campo}`, 'Debe ser una hora HH:MM de 00:00 a 23:59.'))
      }
    }
  })
  return errores
}

/**
 * RN-AG-16 como en la API (H6, D266): en el orden del cuerpo, una franja invertida se informa y no se compara;
 * una no invertida que se superpone con alguna anterior no invertida del mismo día también (aunque esa
 * anterior ya se haya informado).
 */
function erroresDeFranjas(franjas: readonly FranjaFalsa[]): ErrorDeCampoFalso[] {
  const errores: ErrorDeCampoFalso[] = []
  const validas: FranjaFalsa[] = []
  franjas.forEach((franja, i) => {
    if (franja.hora_inicio >= franja.hora_fin) {
      errores.push({
        campo: `franjas.${i}`,
        codigo: 'RN-AG-16',
        mensaje: `franjas.${i} debe terminar después de empezar`,
      })
      return
    }
    const seSuperpone = validas.some(
      (otra) =>
        otra.dia_semana === franja.dia_semana && franja.hora_inicio < otra.hora_fin && otra.hora_inicio < franja.hora_fin,
    )
    if (seSuperpone) {
      errores.push({
        campo: `franjas.${i}`,
        codigo: 'RN-AG-16',
        mensaje: `franjas.${i} se superpone con otra franja del mismo día`,
      })
    }
    validas.push(franja)
  })
  return errores
}

function ordenarFranjas(franjas: readonly FranjaFalsa[]): FranjaFalsa[] {
  return franjas
    .map((f) => ({ dia_semana: f.dia_semana, hora_inicio: f.hora_inicio, hora_fin: f.hora_fin }))
    .sort((a, b) => a.dia_semana - b.dia_semana || a.hora_inicio.localeCompare(b.hora_inicio))
}

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

function rolesValidos(valor: unknown): boolean {
  return (
    Array.isArray(valor) &&
    valor.length >= 1 &&
    valor.length <= ORDEN_DE_ROLES.length &&
    valor.every((rol) => typeof rol === 'string' && ORDEN_DE_ROLES.includes(rol)) &&
    new Set(valor).size === valor.length
  )
}

/** Errores de formato del alta y del `PATCH` de usuarios: lo que valida Pydantic antes que el dominio. */
function erroresDeFormatoDeUsuario(cuerpo: Record<string, unknown> | null, esAlta: boolean): ErrorDeCampoFalso[] {
  if (cuerpo === null) return [errorDeFormato('cuerpo', 'El cuerpo debe ser un objeto JSON.')]
  const errores: ErrorDeCampoFalso[] = []
  const permitidos = esAlta ? CAMPOS_DEL_ALTA_DE_USUARIO : CAMPOS_DEL_PATCH_DE_USUARIO
  for (const campo of Object.keys(cuerpo)) {
    if (!permitidos.has(campo)) errores.push(errorDeFormato(campo, 'Campo no permitido.'))
  }
  if (esAlta) {
    for (const campo of ['email', 'contrasena', 'roles']) {
      if (!(campo in cuerpo)) errores.push(errorDeFormato(campo, 'Campo obligatorio.'))
    }
  }
  const { email, contrasena, roles, activo } = cuerpo
  if (email !== undefined) {
    const recortado = typeof email === 'string' ? email.trim() : ''
    if (recortado.length < 3 || recortado.length > 254 || !FORMATO_DE_EMAIL.test(recortado)) {
      errores.push(errorDeFormato('email', 'Debe ser un email válido de hasta 254 caracteres.'))
    }
  }
  if (contrasena !== undefined && typeof contrasena !== 'string') {
    errores.push(errorDeFormato('contrasena', 'Debe ser un texto.'))
  }
  if (roles !== undefined && !rolesValidos(roles)) {
    errores.push(errorDeFormato('roles', 'Elegí de uno a tres roles distintos.'))
  }
  if (activo !== undefined && typeof activo !== 'boolean') {
    errores.push(errorDeFormato('activo', 'Debe ser verdadero o falso.'))
  }
  return errores
}

function contrasenaFueraDeRango(contrasena: string): boolean {
  return contrasena.length < 10 || new TextEncoder().encode(contrasena).length > 72
}

export function crearServidorFalso(opciones: OpcionesDelServidorFalso = {}): ServidorFalso {
  const catalogo: PrestacionFalsa[] = (opciones.prestaciones ?? []).map((prestacion) => ({ ...prestacion }))
  const usuarios: UsuarioFalso[] = (opciones.usuarios ?? USUARIOS_DE_PARTIDA).map((u) => ({
    ...u,
    roles: [...u.roles],
  }))
  const profesionales: ProfesionalFalso[] = (opciones.profesionales ?? PROFESIONALES_DE_PARTIDA).map((p) => ({ ...p }))
  const horarios = new Map<number, FranjaFalsa[]>(
    profesionales.map((p) => [p.id, ordenarFranjas(opciones.horarios?.[p.id] ?? (p.id === 1 ? HORARIO_DE_LA_DEMO : []))]),
  )
  // Versión del token de cada usuario: desactivar la sube y los tokens anteriores dejan de servir (RN-AU-03).
  const versiones = new Map<number, number>()
  const cuerposRecibidos = new Map<string, Record<string, unknown>[]>()
  const llamadasPorMetodo = new Map<string, number>()
  const contadores = new Map<string, number>()
  let caido = false
  let estado5xx: number | null = null
  let secuencia = 0
  const accesos = new Map<string, { email: string; version: number }>()
  const refrescos = new Map<string, { email: string; version: number }>()
  const sinPermiso = new Set<string>()
  let accessSiempreRechazado = false
  const retenciones = new Map<string, Promise<void>>()

  function usuarioPorEmail(email: string): UsuarioFalso | undefined {
    return usuarios.find((u) => u.email === email)
  }

  function versionDe(email: string): number {
    const usuario = usuarioPorEmail(email)
    return usuario === undefined ? 0 : (versiones.get(usuario.id) ?? 0)
  }

  /** El usuario de un token emitido, si sigue activo y su versión no cambió; si no, undefined (RN-AU-03). */
  function usuarioVigente(emitido: { email: string; version: number } | undefined): UsuarioFalso | undefined {
    if (emitido === undefined) return undefined
    const usuario = usuarioPorEmail(emitido.email)
    if (usuario === undefined || !usuario.activo || versionDe(emitido.email) !== emitido.version) return undefined
    return usuario
  }

  function emitirAccess(email: string): string {
    secuencia += 1
    const token = `acceso-${secuencia}`
    accesos.set(token, { email, version: versionDe(email) })
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

  interface Acceso {
    rechazo: Response | null
    actor: UsuarioFalso | null
  }

  /**
   * Autenticación y permiso (D208: antes que la validación). `permitidos` son los roles que alcanzan; `null`
   * deja pasar a cualquier sesión válida (la lectura de los catálogos). Los roles se leen del catálogo de
   * usuarios en cada petición, como la API real.
   */
  function autorizar(init: RequestInit | undefined, permitidos: readonly string[] | null): Acceso {
    const token = bearer(init)
    const actor = token === null ? undefined : usuarioVigente(accesos.get(token))
    if (actor === undefined || accessSiempreRechazado) return { rechazo: sesionInvalida(), actor: null }
    const alcanza = permitidos === null || actor.roles.some((rol) => permitidos.includes(rol))
    if (sinPermiso.has(actor.email) || !alcanza) {
      const rechazo = problema(403, '/errores/permiso-insuficiente', 'Permiso insuficiente', TEXTO_PERMISO, [
        'RN-AU-05',
      ])
      return { rechazo, actor }
    }
    return { rechazo: null, actor }
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
    return autorizar(init, null).rechazo ?? json(200, catalogo.map((p) => ({ ...p })))
  }

  function crearPrestacion(init: RequestInit | undefined): Response {
    const { rechazo } = autorizar(init, ['odontologo'])
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
    const { rechazo } = autorizar(init, ['odontologo'])
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

  function salidaDeUsuario(usuario: UsuarioFalso): UsuarioFalso {
    return {
      id: usuario.id,
      email: usuario.email,
      roles: ORDEN_DE_ROLES.filter((rol) => usuario.roles.includes(rol)),
      activo: usuario.activo,
    }
  }

  function listarUsuarios(init: RequestInit | undefined): Response {
    const { rechazo } = autorizar(init, ['odontologo', 'dueno'])
    return rechazo ?? json(200, [...usuarios].sort((a, b) => a.id - b.id).map(salidaDeUsuario))
  }

  function crearUsuario(init: RequestInit | undefined): Response {
    const { rechazo } = autorizar(init, ['odontologo'])
    if (rechazo !== null) return rechazo
    const cuerpo = leerCuerpo(init)
    const errores = erroresDeFormatoDeUsuario(cuerpo, true)
    if (cuerpo === null || errores.length > 0) return entradaInvalida(errores, [])
    if (contrasenaFueraDeRango(String(cuerpo.contrasena))) {
      return entradaInvalida([{ campo: 'contrasena', codigo: 'RN-AU-07', mensaje: MENSAJE_RN_AU_07 }], ['RN-AU-07'])
    }
    const email = String(cuerpo.email).trim().toLowerCase()
    if (usuarioPorEmail(email) !== undefined) {
      return problema(409, '/errores/email-repetido', 'Email repetido', 'Ya existe un usuario con ese email.', [
        'RN-AU-08',
      ])
    }
    const nuevo: UsuarioFalso = {
      id: Math.max(0, ...usuarios.map((u) => u.id)) + 1,
      email,
      roles: [...(cuerpo.roles as string[])],
      activo: true,
    }
    usuarios.push(nuevo)
    return json(201, salidaDeUsuario(nuevo))
  }

  function sinOdontologo(detalle: string): Response {
    return problema(409, '/errores/administracion-sin-odontologo', 'Operación no permitida', detalle, ['RN-AU-06'])
  }

  function editarUsuario(id: number, init: RequestInit | undefined): Response {
    const { rechazo, actor } = autorizar(init, ['odontologo'])
    if (rechazo !== null || actor === null) return rechazo ?? sesionInvalida()
    const cuerpo = leerCuerpo(init)
    const errores = erroresDeFormatoDeUsuario(cuerpo, false)
    if (cuerpo === null || errores.length > 0) return entradaInvalida(errores, [])
    const usuario = usuarios.find((u) => u.id === id)
    if (usuario === undefined) {
      return problema(404, '/errores/recurso-no-encontrado', 'Recurso no encontrado', 'No existe.', ['RN-GL-04'], {
        referencias: [{ recurso: 'usuario', recurso_id: id, motivo: 'inexistente' }],
      })
    }
    const rolesPedidos = Array.isArray(cuerpo.roles) ? (cuerpo.roles as string[]) : null
    const activoPedido = typeof cuerpo.activo === 'boolean' ? cuerpo.activo : null
    // RN-AU-06 sobre el resultado combinado del pedido (D252): primero desactivarse, después el último odontólogo.
    if (activoPedido === false && actor.id === usuario.id) return sinOdontologo(DETALLE_DESACTIVARSE)
    const dejaDeSerOdontologoActivo =
      usuario.activo &&
      usuario.roles.includes('odontologo') &&
      ((rolesPedidos !== null && !rolesPedidos.includes('odontologo')) || activoPedido === false)
    const activosDespues = usuarios.filter((u) => u.activo && u.roles.includes('odontologo')).length - 1
    if (dejaDeSerOdontologoActivo && activosDespues === 0) return sinOdontologo(DETALLE_SIN_ODONTOLOGO)
    if (rolesPedidos !== null) usuario.roles = [...rolesPedidos]
    if (activoPedido !== null && activoPedido !== usuario.activo) {
      if (usuario.activo) versiones.set(usuario.id, (versiones.get(usuario.id) ?? 0) + 1)
      usuario.activo = activoPedido
    }
    return json(200, salidaDeUsuario(usuario))
  }

  function profesionalInexistente(id: number): Response {
    return problema(404, '/errores/recurso-no-encontrado', 'Recurso no encontrado', 'No existe.', ['RN-GL-04'], {
      referencias: [{ recurso: 'profesional', recurso_id: id, motivo: 'inexistente' }],
    })
  }

  function salidaDeHorario(id: number): Response {
    return json(200, { profesional_id: id, zona_horaria: ZONA_DEL_CONSULTORIO, franjas: horarios.get(id) ?? [] })
  }

  function listarProfesionales(init: RequestInit | undefined): Response {
    return autorizar(init, null).rechazo ?? json(200, [...profesionales].sort((a, b) => a.id - b.id))
  }

  function leerHorario(id: number, init: RequestInit | undefined): Response {
    const { rechazo } = autorizar(init, null)
    if (rechazo !== null) return rechazo
    return profesionales.some((p) => p.id === id) ? salidaDeHorario(id) : profesionalInexistente(id)
  }

  /** Orden de H8: acceso, formato, `RN-AG-16` (todas juntas) y por último el profesional de la URL (404). */
  function reemplazarHorario(id: number, init: RequestInit | undefined): Response {
    const { rechazo } = autorizar(init, ['odontologo'])
    if (rechazo !== null) return rechazo
    const cuerpo = leerCuerpo(init)
    const errores = erroresDeFormatoDeHorario(cuerpo)
    if (cuerpo === null || errores.length > 0) return entradaInvalida(errores, [])
    const franjas = cuerpo.franjas as FranjaFalsa[]
    const invalidas = erroresDeFranjas(franjas)
    if (invalidas.length > 0) return entradaInvalida(invalidas, ['RN-AG-16'])
    if (!profesionales.some((p) => p.id === id)) return profesionalInexistente(id)
    horarios.set(id, ordenarFranjas(franjas))
    return salidaDeHorario(id)
  }

  async function refrescar(init: RequestInit | undefined): Promise<Response> {
    // Una vuelta del bucle de eventos: da tiempo a que lleguen varios 401 antes de contestar.
    await new Promise<void>((resolver) => setTimeout(resolver, 0))
    const token = leerCuerpo(init)?.refresh_token
    const usuario = typeof token === 'string' ? usuarioVigente(refrescos.get(token)) : undefined
    if (usuario === undefined) return sesionInvalida()
    return json(200, { access_token: emitirAccess(usuario.email), token_type: 'bearer', expires_in: 900 })
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
    refrescos.set(refreshToken, { email: EMAIL_ACTIVA, version: versionDe(EMAIL_ACTIVA) })
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
    if (entrada === '/api/usuarios' && metodo === 'GET') return Promise.resolve(listarUsuarios(init))
    if (entrada === '/api/usuarios' && metodo === 'POST') return Promise.resolve(crearUsuario(init))
    const delPatchDeUsuario = /^\/api\/usuarios\/(\d+)$/.exec(entrada)
    if (delPatchDeUsuario !== null && metodo === 'PATCH') {
      return Promise.resolve(editarUsuario(Number(delPatchDeUsuario[1]), init))
    }
    if (entrada === '/api/profesionales' && metodo === 'GET') return Promise.resolve(listarProfesionales(init))
    const delHorario = /^\/api\/profesionales\/(\d+)\/horario$/.exec(entrada)
    if (delHorario !== null && metodo === 'GET') return Promise.resolve(leerHorario(Number(delHorario[1]), init))
    if (delHorario !== null && metodo === 'PUT') {
      return Promise.resolve(reemplazarHorario(Number(delHorario[1]), init))
    }
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
    usuariosActuales: () => usuarios.map((u) => ({ ...u, roles: [...u.roles] })),
    quitarUsuario: (id) => {
      const indice = usuarios.findIndex((u) => u.id === id)
      if (indice >= 0) usuarios.splice(indice, 1)
    },
    quitarPrestacion: (id) => {
      const indice = catalogo.findIndex((p) => p.id === id)
      if (indice >= 0) catalogo.splice(indice, 1)
    },
    horarioActual: (profesionalId) => (horarios.get(profesionalId) ?? []).map((f) => ({ ...f })),
    quitarProfesional: (id) => {
      const indice = profesionales.findIndex((p) => p.id === id)
      if (indice >= 0) profesionales.splice(indice, 1)
      horarios.delete(id)
    },
    marcarInactivo: (id) => {
      const profesional = profesionales.find((p) => p.id === id)
      if (profesional !== undefined) profesional.activo = false
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
      refrescos.set(refresh, { email, version: versionDe(email) })
      return { access, refresh }
    },
  }
}
