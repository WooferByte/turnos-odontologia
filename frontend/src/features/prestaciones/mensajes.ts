// Textos fijos de la pantalla de prestaciones y el único lugar que decide qué mensaje corresponde a cada
// rechazo (design T6, T11). No se muestra el `detail` de la API.
import { EntradaRechazada, PermisoInsuficiente, ReglaRechazada } from '../../shared/api/errores'

export const SUBTITULO_DE_PANTALLA =
  'Catálogo de prestaciones del consultorio: duración, color en la agenda y reserva online.'
export const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'
export const MENSAJE_LISTA_VACIA = 'Todavía no hay prestaciones.'
export const MENSAJE_CARGANDO = 'Cargando prestaciones…'
export const MENSAJE_NOMBRE_REPETIDO = 'Ya existe una prestación con ese nombre (RN-AG-15).'
export const MENSAJE_DURACION_INVALIDA = 'La duración debe ser mayor que 0 y múltiplo de 5 minutos (RN-AG-01).'
export const MENSAJE_AVISO_DE_DURACION = 'Cambiar la duración no modifica los turnos ya creados.'
export const MENSAJE_PRESTACION_INEXISTENTE = 'La prestación ya no existe (RN-GL-04).'
export const MENSAJE_SIN_PERMISO = 'Tu usuario no tiene permiso para modificar prestaciones (RN-AU-05).'
export const MENSAJE_NOMBRE_VACIO = 'Ingresá un nombre.'
export const MENSAJE_REVISAR_DATOS = 'Revisá los datos de la prestación.'

/** Título corto de un aviso; el `404` y «Revisá los datos…» van sin título porque lo repetirían. */
export function tituloDelAviso(mensaje: string): string | null {
  if (mensaje === MENSAJE_SIN_PERMISO) return 'Acceso restringido'
  if (mensaje === MENSAJE_SIN_CONEXION) return 'Sin conexión'
  return null
}

/** Texto de la insignia del listado general: cuenta activas e inactivas (la tabla muestra ambas). */
export function textoDelContador(cantidad: number): string {
  return cantidad === 1 ? '1 prestación registrada' : `${cantidad} prestaciones registradas`
}

export function subtituloDelPanel(prestacion: { nombre: string } | null): string {
  return prestacion === null
    ? 'Completá los datos de la nueva prestación.'
    : `Modificando los atributos de «${prestacion.nombre}»`
}

/** Lo que el panel lateral muestra después de un rechazo: debajo de cada campo y en el aviso del panel. */
export interface ErroresDelPanel {
  nombre: string | null
  duracion: string | null
  aviso: string | null
}

export const SIN_ERRORES: ErroresDelPanel = { nombre: null, duracion: null, aviso: null }

export function erroresDelPanel(error: unknown): ErroresDelPanel {
  if (error instanceof PermisoInsuficiente) return { ...SIN_ERRORES, aviso: MENSAJE_SIN_PERMISO }
  if (error instanceof ReglaRechazada && error.codigo === 'RN-AG-15') {
    return { ...SIN_ERRORES, nombre: MENSAJE_NOMBRE_REPETIDO }
  }
  if (error instanceof EntradaRechazada) {
    if (error.errores.some((e) => e.campo === 'nombre')) return { ...SIN_ERRORES, nombre: MENSAJE_NOMBRE_VACIO }
    if (error.errores.some((e) => e.campo === 'duracion_minutos' && e.codigo === 'RN-AG-01')) {
      return { ...SIN_ERRORES, duracion: MENSAJE_DURACION_INVALIDA }
    }
    return { ...SIN_ERRORES, aviso: MENSAJE_REVISAR_DATOS }
  }
  return { ...SIN_ERRORES, aviso: MENSAJE_SIN_CONEXION }
}

/** Aviso de la tabla cuando falla una acción de fila (desactivar o reactivar). */
export function avisoDeAccionDeFila(error: unknown): string {
  return error instanceof PermisoInsuficiente ? MENSAJE_SIN_PERMISO : MENSAJE_SIN_CONEXION
}
