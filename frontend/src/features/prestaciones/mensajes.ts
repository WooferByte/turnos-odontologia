// Textos fijos de la pantalla de prestaciones y el único lugar que decide qué mensaje corresponde a cada
// rechazo (design T6, T11). No se muestra el `detail` de la API.
import { EntradaRechazada, ReglaRechazada } from '../../shared/api/errores'

export const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'
export const MENSAJE_LISTA_VACIA = 'Todavía no hay prestaciones.'
export const MENSAJE_CARGANDO = 'Cargando prestaciones…'
export const MENSAJE_NOMBRE_REPETIDO = 'Ya existe una prestación con ese nombre (RN-AG-15).'
export const MENSAJE_NOMBRE_VACIO = 'Ingresá un nombre.'
export const MENSAJE_REVISAR_DATOS = 'Revisá los datos de la prestación.'

/** Lo que el panel lateral muestra después de un rechazo: debajo de cada campo y en el aviso del panel. */
export interface ErroresDelPanel {
  nombre: string | null
  duracion: string | null
  aviso: string | null
}

export const SIN_ERRORES: ErroresDelPanel = { nombre: null, duracion: null, aviso: null }

export function erroresDelPanel(error: unknown): ErroresDelPanel {
  if (error instanceof ReglaRechazada && error.codigo === 'RN-AG-15') {
    return { ...SIN_ERRORES, nombre: MENSAJE_NOMBRE_REPETIDO }
  }
  if (error instanceof EntradaRechazada) {
    if (error.errores.some((e) => e.campo === 'nombre')) return { ...SIN_ERRORES, nombre: MENSAJE_NOMBRE_VACIO }
    return { ...SIN_ERRORES, aviso: MENSAJE_REVISAR_DATOS }
  }
  return { ...SIN_ERRORES, aviso: MENSAJE_SIN_CONEXION }
}
