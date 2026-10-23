// Textos fijos de la pantalla de horario y el único lugar que decide qué mensaje corresponde a cada rechazo
// (design H17). No se muestra el `detail` ni el `mensaje` de la API.
import { EntradaRechazada, PermisoInsuficiente, RecursoInexistente } from '../../shared/api/errores'
import type { Profesional } from './apiHorario'

export const MENSAJE_CARGANDO = 'Cargando horario…'
export const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'
export const MENSAJE_SIN_ATENCION = 'Sin atención'
export const MENSAJE_SIN_PROFESIONALES = 'Todavía no hay profesionales.'
export const MENSAJE_GUARDADO = 'Horario guardado.'
export const MENSAJE_FRANJA_INCOMPLETA = 'Completá las dos horas de la franja.'
export const MENSAJE_RN_AG_16 = 'Hay franjas que se superponen o no terminan después de empezar (RN-AG-16).'
export const MENSAJE_SIN_PERMISO = 'Tu usuario no tiene permiso para modificar el horario (RN-AU-05).'
export const MENSAJE_PROFESIONAL_INEXISTENTE = 'El profesional ya no existe (RN-GL-04).'
export const MENSAJE_REVISAR_FRANJAS = 'Revisá las franjas del horario.'
export const MENSAJE_NOTA_DE_HORARIO =
  'Los turnos solo se pueden crear dentro de una franja (RN-AG-04). Cambiar el horario no modifica los turnos ya dados.'

export function subtituloDeHorario(zonaHoraria: string): string {
  return `Franjas semanales en hora del consultorio (${zonaHoraria}).`
}

/** Nombre del profesional en el selector; el inactivo lleva «(inactivo)» (D267). */
export function etiquetaDelProfesional(profesional: Profesional): string {
  return profesional.activo ? profesional.nombre : `${profesional.nombre} (inactivo)`
}

/** Título corto de un aviso de error; el resto va sin título porque lo repetiría. */
export function tituloDelAviso(mensaje: string): string | null {
  if (mensaje === MENSAJE_SIN_PERMISO) return 'Acceso restringido'
  if (mensaje === MENSAJE_SIN_CONEXION) return 'Sin conexión'
  return null
}

/** Mensaje de la pantalla para un rechazo del `PUT`: por el tipo y el código, nunca por el texto de la API. */
export function mensajeDeRechazo(error: unknown): string {
  if (error instanceof PermisoInsuficiente) return MENSAJE_SIN_PERMISO
  if (error instanceof RecursoInexistente) return MENSAJE_PROFESIONAL_INEXISTENTE
  if (error instanceof EntradaRechazada) {
    return error.codigos.includes('RN-AG-16') ? MENSAJE_RN_AG_16 : MENSAJE_REVISAR_FRANJAS
  }
  return MENSAJE_SIN_CONEXION
}
