// Textos fijos de la pantalla de usuarios y el único lugar que decide qué mensaje corresponde a cada rechazo
// (design U19, como T11 de C-11). No se muestra el `detail` de la API.
import { EntradaRechazada, PermisoInsuficiente, ReglaRechazada } from '../../shared/api/errores'

export const SUBTITULO_DE_PANTALLA = 'Usuarios del consultorio: acceso al panel y roles.'
export const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'
export const MENSAJE_CARGANDO = 'Cargando usuarios…'
export const MENSAJE_SIN_PERMISO_DE_LECTURA = 'Tu usuario no tiene permiso para ver los usuarios (RN-AU-05).'
export const MENSAJE_EMAIL_REPETIDO = 'Ya existe un usuario con ese email (RN-AU-08).'
export const MENSAJE_CONTRASENA_FUERA_DE_RANGO = 'La contraseña debe tener de 10 caracteres a 72 bytes (RN-AU-07).'
export const MENSAJE_SIN_ROLES = 'Elegí al menos un rol.'
export const MENSAJE_EMAIL_INVALIDO = 'Ingresá un email válido.'
export const MENSAJE_REVISAR_DATOS = 'Revisá los datos del usuario.'
export const MENSAJE_SIN_ODONTOLOGO =
  'El consultorio no puede quedar sin un odontólogo activo y nadie puede desactivarse a sí mismo (RN-AU-06).'
export const MENSAJE_USUARIO_INEXISTENTE = 'El usuario ya no existe (RN-GL-04).'
export const MENSAJE_SIN_PERMISO_DE_ESCRITURA = 'Tu usuario no tiene permiso para modificar usuarios (RN-AU-05).'
/** Nota del panel de edición (D254): los roles valen desde la petición siguiente (RN-AU-02). */
export const NOTA_DE_ROLES = 'Quitar o asignar un rol vale desde la próxima acción del usuario, sin cerrar su sesión.'

/** Título corto de un aviso; los demás van sin título porque lo repetirían. */
export function tituloDelAviso(mensaje: string): string | null {
  if (mensaje === MENSAJE_SIN_PERMISO_DE_LECTURA || mensaje === MENSAJE_SIN_PERMISO_DE_ESCRITURA) return 'Acceso restringido'
  if (mensaje === MENSAJE_SIN_CONEXION) return 'Sin conexión'
  if (mensaje === MENSAJE_SIN_ODONTOLOGO) return 'No se pudo completar'
  return null
}

/** Texto de la insignia del listado general: cuenta activos e inactivos (la tabla muestra ambos). */
export function textoDelContador(cantidad: number): string {
  return cantidad === 1 ? '1 usuario registrado' : `${cantidad} usuarios registrados`
}

/** Lo que el panel lateral muestra después de un rechazo: debajo de cada campo y en el aviso del panel. */
export interface ErroresDelPanel {
  email: string | null
  contrasena: string | null
  roles: string | null
  aviso: string | null
}

export const SIN_ERRORES: ErroresDelPanel = { email: null, contrasena: null, roles: null, aviso: null }

function erroresDeEntrada(rechazo: EntradaRechazada): ErroresDelPanel {
  const contrasena = rechazo.errores.some((e) => e.campo === 'contrasena' && e.codigo === 'RN-AU-07')
  const email = rechazo.errores.some((e) => e.campo === 'email')
  const roles = rechazo.errores.some((e) => e.campo === 'roles')
  const conMensajePropio =
    rechazo.errores.length > 0 &&
    rechazo.errores.every(
      (e) => e.campo === 'email' || e.campo === 'roles' || (e.campo === 'contrasena' && e.codigo === 'RN-AU-07'),
    )
  return {
    email: email ? MENSAJE_EMAIL_INVALIDO : null,
    contrasena: contrasena ? MENSAJE_CONTRASENA_FUERA_DE_RANGO : null,
    roles: roles ? MENSAJE_SIN_ROLES : null,
    aviso: conMensajePropio ? null : MENSAJE_REVISAR_DATOS,
  }
}

export function erroresDelPanel(error: unknown): ErroresDelPanel {
  if (error instanceof PermisoInsuficiente) return { ...SIN_ERRORES, aviso: MENSAJE_SIN_PERMISO_DE_ESCRITURA }
  if (error instanceof ReglaRechazada && error.codigo === 'RN-AU-08') {
    return { ...SIN_ERRORES, email: MENSAJE_EMAIL_REPETIDO }
  }
  if (error instanceof ReglaRechazada && error.codigo === 'RN-AU-06') {
    return { ...SIN_ERRORES, aviso: MENSAJE_SIN_ODONTOLOGO }
  }
  if (error instanceof EntradaRechazada) return erroresDeEntrada(error)
  return { ...SIN_ERRORES, aviso: MENSAJE_SIN_CONEXION }
}

export function subtituloDelPanel(usuario: { email: string } | null): string {
  return usuario === null ? 'Completá los datos del nuevo usuario.' : `Modificando los roles de «${usuario.email}»`
}

/** Aviso de la tabla cuando falla una acción de fila (desactivar o reactivar). */
export function avisoDeAccionDeFila(error: unknown): string {
  if (error instanceof PermisoInsuficiente) return MENSAJE_SIN_PERMISO_DE_ESCRITURA
  if (error instanceof ReglaRechazada && error.codigo === 'RN-AU-06') return MENSAJE_SIN_ODONTOLOGO
  return MENSAJE_SIN_CONEXION
}
