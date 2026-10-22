// Textos fijos de la pantalla de usuarios y el único lugar que decide qué mensaje corresponde a cada rechazo
// (design U19, como T11 de C-11). No se muestra el `detail` de la API.
import type { Rol } from './apiUsuarios'

export const SUBTITULO_DE_PANTALLA = 'Usuarios del consultorio: acceso al panel y roles.'
export const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'
export const MENSAJE_CARGANDO = 'Cargando usuarios…'
export const MENSAJE_SIN_PERMISO_DE_LECTURA = 'Tu usuario no tiene permiso para ver los usuarios (RN-AU-05).'

const NOMBRES_DE_ROL: Record<Rol, string> = {
  odontologo: 'Odontólogo',
  recepcionista: 'Recepcionista',
  dueno: 'Dueño',
}

export function nombreDelRol(rol: Rol): string {
  return NOMBRES_DE_ROL[rol]
}

/** Título corto de un aviso; los demás van sin título porque lo repetirían. */
export function tituloDelAviso(mensaje: string): string | null {
  if (mensaje === MENSAJE_SIN_PERMISO_DE_LECTURA) return 'Acceso restringido'
  if (mensaje === MENSAJE_SIN_CONEXION) return 'Sin conexión'
  return null
}

/** Texto de la insignia del listado general: cuenta activos e inactivos (la tabla muestra ambos). */
export function textoDelContador(cantidad: number): string {
  return cantidad === 1 ? '1 usuario registrado' : `${cantidad} usuarios registrados`
}
