// Textos fijos de la pantalla de horario (design H17). No se muestra el `detail` ni el `mensaje` de la API.
import type { Profesional } from './apiHorario'

export const MENSAJE_CARGANDO = 'Cargando horario…'
export const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'
export const MENSAJE_SIN_ATENCION = 'Sin atención'
export const MENSAJE_SIN_PROFESIONALES = 'Todavía no hay profesionales.'
export const MENSAJE_GUARDADO = 'Horario guardado.'
export const MENSAJE_NOTA_DE_HORARIO =
  'Los turnos solo se pueden crear dentro de una franja (RN-AG-04). Cambiar el horario no modifica los turnos ya dados.'

export function subtituloDeHorario(zonaHoraria: string): string {
  return `Franjas semanales en hora del consultorio (${zonaHoraria}).`
}

/** Nombre del profesional en el selector; el inactivo lleva «(inactivo)» (D267). */
export function etiquetaDelProfesional(profesional: Profesional): string {
  return profesional.activo ? profesional.nombre : `${profesional.nombre} (inactivo)`
}

/** Título corto de un aviso de error. */
export function tituloDelAviso(mensaje: string): string | null {
  return mensaje === MENSAJE_SIN_CONEXION ? 'Sin conexión' : null
}
