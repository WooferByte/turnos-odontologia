// Textos fijos de la agenda y el único lugar que decide qué texto corresponde a cada estado (design A12, A15).
// No se muestra el `detail` ni el `mensaje` de la API: la pantalla decide por el tipo de error y por el código.
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
  cancelado_consultorio: 'Cancelado por el consultorio',
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
  cancelado_consultorio: 'rojo',
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
