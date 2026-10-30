// Cliente de la agenda (design A9): habla con `GET /api/turnos`, `POST /api/turnos` y `GET /api/prestaciones` a
// través de la función `pedidoDelPanel` que recibe (inyectada). No evalúa reglas: todo `4xx` pasa por
// `traducirRechazo` y las respuestas `2xx` se validan sin `any`.
import type { PedidoDelPanel } from '../../shared/api/clienteHttp'
import { SinConexion } from '../../shared/api/errores'
import { traducirRechazo } from '../../shared/api/rechazos'
import { crearApiPrestaciones, type Prestacion } from '../prestaciones/apiPrestaciones'

export const ESTADOS_DEL_TURNO = [
  'pendiente_aprobacion',
  'pendiente_sena',
  'reservado',
  'confirmado',
  'cancelado_paciente',
  'cancelado_profesional',
  'vencido',
  'atendido',
  'ausente',
] as const

export type EstadoDelTurno = (typeof ESTADOS_DEL_TURNO)[number]

/** Los estados activos de RN-AG-10: los únicos turnos que se reprograman (design M11). */
export const ESTADOS_ACTIVOS_DEL_TURNO: readonly EstadoDelTurno[] = [
  'pendiente_aprobacion',
  'pendiente_sena',
  'reservado',
  'confirmado',
]

/** Los dos estados a los que se cancela un turno: quién pidió la cancelación (D342). */
export type EstadoDeCancelacion = 'cancelado_paciente' | 'cancelado_profesional'

/** Los estados desde los que se registra la asistencia: solo `reservado` y `confirmado` (design W12). */
export const ESTADOS_QUE_SE_MARCAN_DEL_TURNO: readonly EstadoDelTurno[] = ['reservado', 'confirmado']

/** Los dos estados a los que se marca un turno: cómo terminó. */
export type EstadoDeAsistencia = 'atendido' | 'ausente'

export interface TurnoDeLaAgenda {
  id: number
  /** ISO en UTC con `Z`. */
  inicio: string
  fin: string
  duracion_minutos: number
  estado: EstadoDelTurno
  profesional_id: number
  sillon_id: number
  paciente: { id: number; nombre: string; apellido: string }
  prestacion: { id: number; nombre: string; color: string }
}

export interface AgendaDelDia {
  /** `aaaa-mm-dd`, el día del consultorio. */
  fecha: string
  zona_horaria: string
  turnos: TurnoDeLaAgenda[]
}

/** Cuerpo del alta: sin profesional ni sillón (RN-AG-14). */
export interface NuevoTurno {
  paciente_id: number
  prestacion_id: number
  inicio: string
}

export interface TurnoCreado {
  id: number
  paciente_id: number
  prestacion_id: number
  inicio: string
  fin: string
  estado: string
}

/** Cuerpo de la reprogramación: el inicio nuevo en UTC y la duración (design M2). */
export interface ReprogramacionDeTurno {
  inicio: string
  duracion_minutos: number
}

/** El turno reprogramado: la forma de `TurnoSalida`. */
export interface TurnoReprogramado extends TurnoCreado {
  duracion_minutos: number
}

const RUTA = '/api/turnos'
const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor.'

function esObjeto(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === 'object' && valor !== null
}

function esEstado(valor: unknown): valor is EstadoDelTurno {
  return typeof valor === 'string' && (ESTADOS_DEL_TURNO as readonly string[]).includes(valor)
}

function esTurno(valor: unknown): valor is TurnoDeLaAgenda {
  if (!esObjeto(valor)) return false
  const { paciente, prestacion } = valor
  return (
    typeof valor.id === 'number' &&
    typeof valor.inicio === 'string' &&
    typeof valor.fin === 'string' &&
    typeof valor.duracion_minutos === 'number' &&
    esEstado(valor.estado) &&
    typeof valor.profesional_id === 'number' &&
    typeof valor.sillon_id === 'number' &&
    esObjeto(paciente) &&
    typeof paciente.id === 'number' &&
    typeof paciente.nombre === 'string' &&
    typeof paciente.apellido === 'string' &&
    esObjeto(prestacion) &&
    typeof prestacion.id === 'number' &&
    typeof prestacion.nombre === 'string' &&
    typeof prestacion.color === 'string'
  )
}

function esAgenda(valor: unknown): valor is AgendaDelDia {
  return (
    esObjeto(valor) &&
    typeof valor.fecha === 'string' &&
    typeof valor.zona_horaria === 'string' &&
    Array.isArray(valor.turnos) &&
    valor.turnos.every(esTurno)
  )
}

function esTurnoCreado(valor: unknown): valor is TurnoCreado {
  return (
    esObjeto(valor) &&
    typeof valor.id === 'number' &&
    typeof valor.paciente_id === 'number' &&
    typeof valor.prestacion_id === 'number' &&
    typeof valor.inicio === 'string' &&
    typeof valor.fin === 'string' &&
    typeof valor.estado === 'string'
  )
}

function esTurnoReprogramado(valor: unknown): valor is TurnoReprogramado {
  return esTurnoCreado(valor) && typeof (valor as { duracion_minutos?: unknown }).duracion_minutos === 'number'
}

async function leerJson(respuesta: Response): Promise<unknown> {
  if (!respuesta.ok) throw await traducirRechazo(respuesta)
  try {
    return await respuesta.json()
  } catch {
    throw new SinConexion(MENSAJE_SIN_CONEXION, null)
  }
}

export interface ApiAgenda {
  /** Sin `fecha`, la API devuelve el día de hoy del consultorio. */
  obtenerAgenda(fecha?: string): Promise<AgendaDelDia>
  crearTurno(nuevo: NuevoTurno): Promise<TurnoCreado>
  reprogramarTurno(id: number, cambio: ReprogramacionDeTurno): Promise<TurnoReprogramado>
  cancelarTurno(id: number, estado: EstadoDeCancelacion): Promise<TurnoReprogramado>
  marcarAsistencia(id: number, estado: EstadoDeAsistencia): Promise<TurnoReprogramado>
  obtenerPrestacionesActivas(): Promise<Prestacion[]>
}

export function crearApiAgenda(pedidoDelPanel: PedidoDelPanel): ApiAgenda {
  const prestaciones = crearApiPrestaciones(pedidoDelPanel)
  return {
    async obtenerAgenda(fecha) {
      const ruta = fecha === undefined ? RUTA : `${RUTA}?fecha=${fecha}`
      const cuerpo = await leerJson(await pedidoDelPanel(ruta))
      if (!esAgenda(cuerpo)) throw new SinConexion(MENSAJE_SIN_CONEXION, null)
      return cuerpo
    },
    async crearTurno(nuevo) {
      const init: RequestInit = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(nuevo),
      }
      const cuerpo = await leerJson(await pedidoDelPanel(RUTA, init))
      if (!esTurnoCreado(cuerpo)) throw new SinConexion(MENSAJE_SIN_CONEXION, null)
      return cuerpo
    },
    async reprogramarTurno(id, cambio) {
      const init: RequestInit = {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cambio),
      }
      const cuerpo = await leerJson(await pedidoDelPanel(`${RUTA}/${id}`, init))
      if (!esTurnoReprogramado(cuerpo)) throw new SinConexion(MENSAJE_SIN_CONEXION, null)
      return cuerpo
    },
    async cancelarTurno(id, estado) {
      const init: RequestInit = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ estado }),
      }
      const cuerpo = await leerJson(await pedidoDelPanel(`${RUTA}/${id}/cancelar`, init))
      if (!esTurnoReprogramado(cuerpo)) throw new SinConexion(MENSAJE_SIN_CONEXION, null)
      return cuerpo
    },
    async marcarAsistencia(id, estado) {
      const init: RequestInit = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ estado }),
      }
      const cuerpo = await leerJson(await pedidoDelPanel(`${RUTA}/${id}/estado`, init))
      if (!esTurnoReprogramado(cuerpo)) throw new SinConexion(MENSAJE_SIN_CONEXION, null)
      return cuerpo
    },
    async obtenerPrestacionesActivas() {
      return (await prestaciones.listarPrestaciones()).filter((p) => p.activa)
    },
  }
}
