// Textos fijos del panel del historial y las funciones puras que arman cada entrada (design G4, G5, G6). No se
// muestra el `detail` de la API: la pantalla decide por el tipo de error y por el código (D323).
import { fechaLocal, horaLocal } from '../../shared/horaDelConsultorio'
import { ESTADOS_DEL_TURNO, type EstadoDelTurno } from '../agenda/apiAgenda'
import { ETIQUETAS_DE_ESTADO, nombreDelDia } from '../agenda/mensajes'

export const TITULO_DEL_PANEL = 'Historial del turno'
export const MENSAJE_SOLO_LECTURA = 'Solo lectura: el historial no se puede editar.'
export const MENSAJE_CARGANDO = 'Cargando historial…'
export const MENSAJE_SIN_EVENTOS = 'Este turno no tiene eventos registrados.'
export const MENSAJE_TURNO_INEXISTENTE = 'El turno ya no existe (RN-GL-04).'
export const MENSAJE_SIN_PERMISO = 'Tu usuario no tiene permiso para ver el historial (RN-AU-05).'
export const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'

const ACTOR_SIN_IDENTIFICAR = 'Por: Usuario del panel (sin identificar)'

const TITULOS_DE_EVENTO: Readonly<Record<string, string>> = {
  creado: 'Turno creado',
  reprogramado: 'Turno reprogramado',
}

/** «Turno creado» o «Turno reprogramado»; un tipo que la pantalla todavía no conoce se ve igual, sin ocultarlo (G5). */
export function tituloDelEvento(tipo: string): string {
  return TITULOS_DE_EVENTO[tipo] ?? `Cambio registrado (${tipo})`
}

/** «lunes 26 de octubre de 2026, 10:15» en hora del consultorio (RN-GL-01). */
export function cuandoOcurrio(ocurridoEn: string, zona: string): string {
  return `${nombreDelDia(fechaLocal(ocurridoEn, zona))}, ${horaLocal(ocurridoEn, zona)}`
}

/** «Por: Usuario n.º 2»; sin id, «Usuario del panel (sin identificar)»; un tipo desconocido, tal cual (G4, D328). */
export function textoDelActor(actorTipo: string, actorId: string | null): string {
  if (actorTipo !== 'usuario') return `Por: ${actorTipo}`
  return actorId === null ? ACTOR_SIN_IDENTIFICAR : `Por: Usuario n.º ${actorId}`
}

function esEstado(valor: unknown): valor is EstadoDelTurno {
  return typeof valor === 'string' && (ESTADOS_DEL_TURNO as readonly string[]).includes(valor)
}

/** «Estado inicial: Reservado · 09:00 – 09:30»; `null` si `despues` no trae un estado conocido y un inicio y fin de texto (G5). */
export function detalleDelCreado(despues: Record<string, unknown> | null, zona: string): string | null {
  if (despues === null) return null
  const { estado, inicio, fin } = despues
  if (!esEstado(estado) || typeof inicio !== 'string' || typeof fin !== 'string') return null
  return `Estado inicial: ${ETIQUETAS_DE_ESTADO[estado]} · ${horaLocal(inicio, zona)} – ${horaLocal(fin, zona)}`
}

interface HorarioDelTurno {
  inicio: string
  fin: string
  duracion: number
}

function horarioDe(foto: Record<string, unknown> | null): HorarioDelTurno | null {
  if (foto === null) return null
  const { inicio, fin, duracion_minutos: duracion } = foto
  if (typeof inicio !== 'string' || typeof fin !== 'string' || typeof duracion !== 'number') return null
  return Number.isInteger(duracion) ? { inicio, fin, duracion } : null
}

function lineaDelHorario(rotulo: string, horario: HorarioDelTurno, zona: string): string {
  const dia = nombreDelDia(fechaLocal(horario.inicio, zona))
  return `${rotulo}: ${dia}, ${horaLocal(horario.inicio, zona)} – ${horaLocal(horario.fin, zona)} (${horario.duracion} min)`
}

/**
 * Las líneas «Antes: …» y «Después: …» de un `reprogramado` (D340), con el día completo aunque no cambie; ninguna si
 * `antes` o `despues` no traen un inicio y un fin de texto y una duración entera.
 */
export function detalleDelReprogramado(
  antes: Record<string, unknown> | null,
  despues: Record<string, unknown> | null,
  zona: string,
): string[] {
  const horarioAntes = horarioDe(antes)
  const horarioDespues = horarioDe(despues)
  if (horarioAntes === null || horarioDespues === null) return []
  return [lineaDelHorario('Antes', horarioAntes, zona), lineaDelHorario('Después', horarioDespues, zona)]
}
