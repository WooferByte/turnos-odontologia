// Textos fijos de la pantalla de bloqueos y el único lugar que decide qué mensaje corresponde a cada rechazo
// (design B17). No se muestra el `detail` ni el `mensaje` de la API.
import { EntradaRechazada, PermisoInsuficiente, RecursoInexistente } from '../../shared/api/errores'
import type { Profesional } from '../horario/apiHorario'
import type { Bloqueo, Sillon, TurnoAfectado } from './apiBloqueos'
import { aLocal } from '../../shared/horaDelConsultorio'

export const MENSAJE_CARGANDO = 'Cargando bloqueos…'
export const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'
export const MENSAJE_SIN_BLOQUEOS = 'No hay bloqueos cargados.'
export const MENSAJE_FORMULARIO_INCOMPLETO = 'Completá alcance, desde, hasta y motivo.'
export const MENSAJE_ELIMINADO = 'Bloqueo eliminado.'
export const MENSAJE_RN_AG_17 = 'El bloqueo tiene que terminar después de empezar (RN-AG-17).'
export const MENSAJE_RECURSO_NO_DISPONIBLE = 'El profesional o el sillón elegido ya no está disponible (RN-GL-04).'
export const MENSAJE_BLOQUEO_INEXISTENTE = 'El bloqueo ya no existe (RN-GL-04).'
export const MENSAJE_SIN_PERMISO = 'Tu usuario no tiene permiso para modificar los bloqueos (RN-AU-05).'
export const MENSAJE_REVISAR_DATOS = 'Revisá los datos del bloqueo.'
export const MENSAJE_NOTA_DE_BLOQUEOS =
  'Un bloqueo impide dar turnos en ese horario (RN-AG-04b). Los turnos que ya estaban no se cancelan.'

export function subtituloDeBloqueos(zonaHoraria: string): string {
  return `Fechas y horas del consultorio (${zonaHoraria}).`
}

/** «Todo el consultorio», «Profesional: <nombre>» o «Sillón: <nombre>» (los nombres salen de las listas de la API). */
export function etiquetaDelAlcance(
  bloqueo: Bloqueo,
  profesionales: readonly Profesional[],
  sillones: readonly Sillon[],
): string {
  if (bloqueo.alcance === 'profesional') {
    const profesional = profesionales.find((p) => p.id === bloqueo.profesional_id)
    return `Profesional: ${profesional?.nombre ?? `Nº ${bloqueo.profesional_id}`}`
  }
  if (bloqueo.alcance === 'sillon') {
    const sillon = sillones.find((s) => s.id === bloqueo.sillon_id)
    return `Sillón: ${sillon?.nombre ?? `Nº ${bloqueo.sillon_id}`}`
  }
  return 'Todo el consultorio'
}

/** Aviso del `201`: dice cuántos turnos activos quedaron adentro y que no se cancelaron (US-003 CA-2, D83). */
export function avisoDeCreado(turnosAfectados: number): string {
  if (turnosAfectados === 0) return 'Bloqueo creado. No hay turnos activos en ese horario.'
  if (turnosAfectados === 1) {
    return 'Bloqueo creado. Hay 1 turno activo en ese horario: no se canceló, hay que reprogramarlo o cancelarlo.'
  }
  return `Bloqueo creado. Hay ${turnosAfectados} turnos activos en ese horario: no se cancelaron, hay que reprogramarlos o cancelarlos.`
}

/** «Turno 7 · 02/11/2026 10:00 a 10:30» en hora del consultorio; el estado va aparte, como etiqueta. */
export function filaDeTurnoAfectado(turno: TurnoAfectado, zonaHoraria: string): string {
  const desde = aLocal(turno.inicio, zonaHoraria)
  const hasta = aLocal(turno.fin, zonaHoraria).slice(-5)
  return `Turno ${turno.id} · ${desde} a ${hasta}`
}

/** Título corto de un aviso de error; el resto va sin título porque lo repetiría. */
export function tituloDelAviso(mensaje: string): string | null {
  if (mensaje === MENSAJE_SIN_PERMISO) return 'Acceso restringido'
  if (mensaje === MENSAJE_SIN_CONEXION) return 'Sin conexión'
  return null
}

export type Accion = 'crear' | 'eliminar'

/** Mensaje de la pantalla para un rechazo: por el tipo y el código, nunca por el texto de la API. */
export function mensajeDeRechazo(error: unknown, accion: Accion): string {
  if (error instanceof PermisoInsuficiente) return MENSAJE_SIN_PERMISO
  if (error instanceof RecursoInexistente) {
    return accion === 'eliminar' ? MENSAJE_BLOQUEO_INEXISTENTE : MENSAJE_RECURSO_NO_DISPONIBLE
  }
  if (error instanceof EntradaRechazada) {
    if (error.codigos.includes('RN-GL-04')) return MENSAJE_RECURSO_NO_DISPONIBLE
    if (error.codigos.includes('RN-AG-17')) return MENSAJE_RN_AG_17
    return MENSAJE_REVISAR_DATOS
  }
  return MENSAJE_SIN_CONEXION
}
