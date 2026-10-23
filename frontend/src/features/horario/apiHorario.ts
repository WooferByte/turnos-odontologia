// Cliente del horario recurrente (design H14): habla con `GET /api/profesionales` y con
// `GET/PUT /api/profesionales/{id}/horario` a través de la función `pedidoDelPanel` que recibe (inyectada).
// No evalúa reglas: todo `4xx` pasa por `traducirRechazo`.
import type { PedidoDelPanel } from '../../shared/api/clienteHttp'
import { SinConexion } from '../../shared/api/errores'
import { traducirRechazo } from '../../shared/api/rechazos'

export interface Profesional {
  id: number
  nombre: string
  activo: boolean
}

/** Una franja semanal: `dia_semana` 0 (lunes) a 6 (domingo) y horas `HH:MM` del consultorio. */
export interface Franja {
  dia_semana: number
  hora_inicio: string
  hora_fin: string
}

export interface HorarioDelProfesional {
  profesional_id: number
  zona_horaria: string
  franjas: Franja[]
}

const RUTA = '/api/profesionales'
const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor.'

function esObjeto(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === 'object' && valor !== null
}

function esProfesional(valor: unknown): valor is Profesional {
  return (
    esObjeto(valor) &&
    typeof valor.id === 'number' &&
    typeof valor.nombre === 'string' &&
    typeof valor.activo === 'boolean'
  )
}

function esFranja(valor: unknown): valor is Franja {
  return (
    esObjeto(valor) &&
    typeof valor.dia_semana === 'number' &&
    typeof valor.hora_inicio === 'string' &&
    typeof valor.hora_fin === 'string'
  )
}

function esHorario(valor: unknown): valor is HorarioDelProfesional {
  return (
    esObjeto(valor) &&
    typeof valor.profesional_id === 'number' &&
    typeof valor.zona_horaria === 'string' &&
    Array.isArray(valor.franjas) &&
    valor.franjas.every(esFranja)
  )
}

async function leerJson(respuesta: Response): Promise<unknown> {
  if (!respuesta.ok) throw await traducirRechazo(respuesta)
  try {
    return await respuesta.json()
  } catch {
    throw new SinConexion(MENSAJE_SIN_CONEXION, null)
  }
}

async function leerHorario(respuesta: Response): Promise<HorarioDelProfesional> {
  const cuerpo = await leerJson(respuesta)
  if (!esHorario(cuerpo)) throw new SinConexion(MENSAJE_SIN_CONEXION, null)
  return cuerpo
}

export interface ApiHorario {
  listarProfesionales(): Promise<Profesional[]>
  obtenerHorario(profesionalId: number): Promise<HorarioDelProfesional>
  reemplazarHorario(profesionalId: number, franjas: readonly Franja[]): Promise<HorarioDelProfesional>
}

export function crearApiHorario(pedidoDelPanel: PedidoDelPanel): ApiHorario {
  return {
    async listarProfesionales() {
      const cuerpo = await leerJson(await pedidoDelPanel(RUTA))
      if (!Array.isArray(cuerpo) || !cuerpo.every(esProfesional)) throw new SinConexion(MENSAJE_SIN_CONEXION, null)
      return cuerpo
    },
    async obtenerHorario(profesionalId) {
      return leerHorario(await pedidoDelPanel(`${RUTA}/${profesionalId}/horario`))
    },
    async reemplazarHorario(profesionalId, franjas) {
      const init: RequestInit = {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ franjas }),
      }
      return leerHorario(await pedidoDelPanel(`${RUTA}/${profesionalId}/horario`, init))
    },
  }
}
