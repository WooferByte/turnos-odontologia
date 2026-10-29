// Textos fijos de la agenda y el único lugar que decide qué texto corresponde a cada estado (design A12, A15).
// No se muestra el `detail` ni el `mensaje` de la API: la pantalla decide por el tipo de error y por el código.
import {
  EntradaRechazada,
  PermisoInsuficiente,
  RecursoInexistente,
  ReglaRechazada,
  type ReferenciaRechazada,
} from '../../shared/api/errores'
import type { EstadoDelTurno } from './apiAgenda'

export const MENSAJE_CARGANDO = 'Cargando agenda…'
export const MENSAJE_SIN_TURNOS = 'No hay turnos para este día.'
export const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'
export const MENSAJE_SIN_PERMISO_PARA_VER = 'Tu usuario no tiene permiso para ver la agenda (RN-AU-05).'

export const ETIQUETAS_DE_ESTADO: Readonly<Record<EstadoDelTurno, string>> = {
  pendiente_aprobacion: 'Pendiente de aprobación',
  pendiente_sena: 'Pendiente de seña',
  reservado: 'Reservado',
  confirmado: 'Confirmado',
  cancelado_paciente: 'Cancelado por el paciente',
  cancelado_profesional: 'Cancelado por el consultorio',
  vencido: 'Vencido',
  atendido: 'Atendido',
  ausente: 'Ausente',
}

export type TonoDeEstado = 'celeste' | 'verde' | 'ambar' | 'rojo'

/** Celeste para `reservado`, verde para `confirmado` y `atendido`, ámbar para los dos pendientes y rojo suave para el resto. */
export const TONOS_DE_ESTADO: Readonly<Record<EstadoDelTurno, TonoDeEstado>> = {
  pendiente_aprobacion: 'ambar',
  pendiente_sena: 'ambar',
  reservado: 'celeste',
  confirmado: 'verde',
  cancelado_paciente: 'rojo',
  cancelado_profesional: 'rojo',
  vencido: 'rojo',
  atendido: 'verde',
  ausente: 'rojo',
}

const DIAS_DE_LA_SEMANA = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'] as const
const MESES = [
  'enero',
  'febrero',
  'marzo',
  'abril',
  'mayo',
  'junio',
  'julio',
  'agosto',
  'septiembre',
  'octubre',
  'noviembre',
  'diciembre',
] as const

const FECHA_DEL_DIA = /^(\d{4})-(\d{2})-(\d{2})$/

function partesDe(fecha: string): { anio: number; mes: number; dia: number } {
  const coincidencia = FECHA_DEL_DIA.exec(fecha)
  if (coincidencia === null) throw new RangeError(`Fecha inválida: ${fecha}`)
  const [anio, mes, dia] = coincidencia.slice(1).map(Number)
  return { anio: anio ?? 0, mes: mes ?? 1, dia: dia ?? 1 }
}

function instanteDeLaFecha(fecha: string): Date {
  const { anio, mes, dia } = partesDe(fecha)
  return new Date(Date.UTC(anio, mes - 1, dia))
}

function dosCifras(n: number): string {
  return String(n).padStart(2, '0')
}

/** «lunes 2 de noviembre de 2026»: armado con listas fijas porque el ICU de cada navegador agrega una coma (V2). */
export function nombreDelDia(fecha: string): string {
  const { anio, mes, dia } = partesDe(fecha)
  const semana = DIAS_DE_LA_SEMANA[instanteDeLaFecha(fecha).getUTCDay()] ?? ''
  return `${semana} ${dia} de ${MESES[mes - 1] ?? ''} de ${anio}`
}

/** «lun 02/11/2026», el nombre corto del día para anchos angostos. */
export function diaCompacto(fecha: string): string {
  const { anio, mes, dia } = partesDe(fecha)
  const semana = (DIAS_DE_LA_SEMANA[instanteDeLaFecha(fecha).getUTCDay()] ?? '').slice(0, 3)
  return `${semana} ${dosCifras(dia)}/${dosCifras(mes)}/${anio}`
}

/** Suma o resta días de calendario a una fecha `aaaa-mm-dd`, sin hora ni zona (cruza fin de mes y de año). */
export function sumarDias(fecha: string, dias: number): string {
  const instante = instanteDeLaFecha(fecha)
  instante.setUTCDate(instante.getUTCDate() + dias)
  return `${instante.getUTCFullYear()}-${dosCifras(instante.getUTCMonth() + 1)}-${dosCifras(instante.getUTCDate())}`
}

export function subtituloDeAgenda(zonaHoraria: string): string {
  return `Horas del consultorio (${zonaHoraria}).`
}

export function textoDelContador(cantidad: number): string {
  return cantidad === 1 ? '1 turno' : `${cantidad} turnos`
}

/** Título corto de un aviso de error; el resto va sin título porque lo repetiría. */
export function tituloDelAviso(mensaje: string): string | null {
  if (mensaje === MENSAJE_SIN_PERMISO_PARA_VER) return 'Acceso restringido'
  if (mensaje === MENSAJE_SIN_CONEXION) return 'Sin conexión'
  return null
}

export const MENSAJE_FORMULARIO_INCOMPLETO = 'Completá paciente, prestación, fecha y hora.'
export const MENSAJE_TURNO_CREADO = 'Turno creado.'
export const MENSAJE_REVISAR_DATOS = 'Revisá los datos del turno.'
export const MENSAJE_SIN_PERMISO_PARA_CREAR = 'Tu usuario no tiene permiso para crear turnos (RN-AU-05).'

const MENSAJE_E4 = 'El profesional y el sillón ya tienen un turno activo en ese horario (RN-AG-05, RN-AG-08).'
const MENSAJE_RN_AG_05 = 'El profesional ya tiene un turno activo en ese horario (RN-AG-05).'
const MENSAJE_RN_AG_08 = 'El sillón ya tiene un turno activo en ese horario (RN-AG-08).'
const MENSAJE_RN_AG_04 = 'El turno no cae dentro del horario de atención del profesional (RN-AG-04).'
const MENSAJE_RN_AG_04B = 'Ese horario está bloqueado (RN-AG-04b).'
const MENSAJE_RN_AG_10D = 'El turno no puede pasar de la medianoche del consultorio (RN-AG-10d).'
const MENSAJE_RN_GL_01 = 'La fecha y hora no es válida (RN-GL-01).'

const NOMBRES_DE_RECURSO: Readonly<Record<string, string>> = {
  paciente: 'paciente',
  prestacion: 'prestación',
  profesional: 'profesional',
  sillon: 'sillón',
}

/** «no existe», «inactiva»/«inactivo» según el recurso, «no hay ninguno activo» o «hay más de uno activo». */
function textoDelMotivo(recurso: string, motivo: string): string {
  if (motivo === 'inexistente') return 'no existe'
  if (motivo === 'inactivo') return recurso === 'prestacion' ? 'inactiva' : 'inactivo'
  if (motivo === 'ninguno_activo') return 'no hay ninguno activo'
  if (motivo === 'varios_activos') return 'hay más de uno activo'
  return motivo
}

/** «paciente 99 (no existe)»; sin id cuando el dato se omitió (el profesional o el sillón únicos). */
export function textoDeReferencia(referencia: ReferenciaRechazada): string {
  const nombre = NOMBRES_DE_RECURSO[referencia.recurso] ?? referencia.recurso
  const id = referencia.recurso_id === null ? '' : ` ${referencia.recurso_id}`
  return `${nombre}${id} (${textoDelMotivo(referencia.recurso, referencia.motivo)})`
}

function mensajeDeEntradaRechazada(error: EntradaRechazada): string {
  const { codigos } = error
  if (codigos.includes('RN-GL-04')) {
    const referencias = error.referencias.map(textoDeReferencia).join(', ')
    return `Hay datos que no existen o no están activos: ${referencias} (RN-GL-04).`
  }
  if (codigos.includes('RN-AG-04b')) return MENSAJE_RN_AG_04B
  if (codigos.includes('RN-AG-04')) return MENSAJE_RN_AG_04
  if (codigos.includes('RN-AG-10d')) return MENSAJE_RN_AG_10D
  if (codigos.includes('RN-GL-01')) return MENSAJE_RN_GL_01
  return MENSAJE_REVISAR_DATOS
}

function mensajeDeReglaRechazada(error: ReglaRechazada): string {
  const { codigos } = error
  if (codigos.includes('RN-AG-05') && codigos.includes('RN-AG-08')) return MENSAJE_E4
  if (codigos.includes('RN-AG-05')) return MENSAJE_RN_AG_05
  if (codigos.includes('RN-AG-08')) return MENSAJE_RN_AG_08
  return MENSAJE_REVISAR_DATOS
}

/** Mensaje del panel para un rechazo de `POST /turnos`: por el tipo y el código, nunca por el texto de la API. */
export function mensajeDeCreacion(error: unknown): string {
  if (error instanceof PermisoInsuficiente) return MENSAJE_SIN_PERMISO_PARA_CREAR
  if (error instanceof ReglaRechazada) return mensajeDeReglaRechazada(error)
  if (error instanceof EntradaRechazada) return mensajeDeEntradaRechazada(error)
  return MENSAJE_SIN_CONEXION
}

export function textoDeFin(hora: string): string {
  return `Termina a las ${hora}.`
}

export const MENSAJE_TURNO_REPROGRAMADO = 'Turno reprogramado.'
export const MENSAJE_EL_TURNO_NO_CAMBIO = 'El turno no cambió.'
export const MENSAJE_REPROGRAMACION_INCOMPLETA = 'Completá fecha, hora y duración.'
export const MENSAJE_SIN_CAMBIOS = 'No cambiaste la fecha, la hora ni la duración.'
const MENSAJE_RN_AG_01 = 'La duración debe ser mayor que 0 y múltiplo de 5 minutos (RN-AG-01).'
const MENSAJE_RN_AG_18 = 'Este turno ya no se puede reprogramar por su estado (RN-AG-18).'
const MENSAJE_TURNO_INEXISTENTE = 'El turno ya no existe (RN-GL-04).'
const MENSAJE_SIN_PERMISO_PARA_REPROGRAMAR = 'Tu usuario no tiene permiso para reprogramar turnos (RN-AU-05).'

/**
 * Mensaje del panel para un rechazo de `PATCH /turnos/{id}`: por el tipo y el código, nunca por el texto de la API.
 * Reusa los textos de los códigos que comparte con el alta; el panel le suma «El turno no cambió.».
 */
export function mensajeDeReprogramacion(error: unknown): string {
  if (error instanceof PermisoInsuficiente) return MENSAJE_SIN_PERMISO_PARA_REPROGRAMAR
  if (error instanceof RecursoInexistente) return MENSAJE_TURNO_INEXISTENTE
  if (error instanceof ReglaRechazada) {
    return error.codigos.includes('RN-AG-18') ? MENSAJE_RN_AG_18 : mensajeDeReglaRechazada(error)
  }
  if (error instanceof EntradaRechazada) {
    return error.codigos.includes('RN-AG-01') ? MENSAJE_RN_AG_01 : mensajeDeEntradaRechazada(error)
  }
  return MENSAJE_SIN_CONEXION
}

export const MENSAJE_TURNO_CANCELADO = 'Turno cancelado.'
export const MENSAJE_ELEGI_QUIEN_PIDIO = 'Elegí quién pidió la cancelación.'
export const PREGUNTA_DE_CANCELACION = '¿Quién pidió la cancelación?'
export const OPCION_EL_PACIENTE = 'El paciente'
export const OPCION_EL_CONSULTORIO = 'El consultorio'
export const AYUDA_DE_CANCELACION = 'El horario queda libre para otro turno.'
const MENSAJE_RN_AG_12 = 'Este turno ya no se puede cancelar por su estado (RN-AG-12).'
const MENSAJE_SIN_PERMISO_PARA_CANCELAR = 'Tu usuario no tiene permiso para cancelar turnos (RN-AU-05).'

/**
 * Mensaje del panel para un rechazo de `POST /turnos/{id}/cancelar`: por el tipo y el código, nunca por el texto de
 * la API. Un `422` o un `5xx` no pueden salir de esta pantalla y se ven como el aviso de conexión (design X9).
 */
export function mensajeDeCancelacion(error: unknown): string {
  if (error instanceof PermisoInsuficiente) return MENSAJE_SIN_PERMISO_PARA_CANCELAR
  if (error instanceof RecursoInexistente) return MENSAJE_TURNO_INEXISTENTE
  if (error instanceof ReglaRechazada && error.codigos.includes('RN-AG-12')) return MENSAJE_RN_AG_12
  return MENSAJE_SIN_CONEXION
}
