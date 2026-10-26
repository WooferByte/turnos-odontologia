// Cliente de los bloqueos (design B14): habla con `GET/POST /api/bloqueos`, `DELETE /api/bloqueos/{id}` y
// `GET /api/sillones` a través de la función `pedidoDelPanel` que recibe (inyectada). No evalúa reglas: todo
// `4xx` pasa por `traducirRechazo` y las respuestas `2xx` se validan sin `any`.
import type { PedidoDelPanel } from '../../shared/api/clienteHttp'
import { SinConexion } from '../../shared/api/errores'
import { traducirRechazo } from '../../shared/api/rechazos'

export interface Sillon {
  id: number
  nombre: string
  activo: boolean
}

export interface Bloqueo {
  id: number
  alcance: 'profesional' | 'sillon' | 'consultorio'
  profesional_id: number | null
  sillon_id: number | null
  /** ISO en UTC con `Z`. */
  inicio: string
  fin: string
  motivo: string
  creado_por: number
}

/** Un turno activo dentro del bloqueo; sin datos del paciente más que su id (D275). */
export interface TurnoAfectado {
  id: number
  inicio: string
  fin: string
  estado: string
  profesional_id: number
  sillon_id: number
  paciente_id: number
}

export interface BloqueoCreado extends Bloqueo {
  turnos_afectados: TurnoAfectado[]
}

export interface BloqueosDelConsultorio {
  zona_horaria: string
  bloqueos: Bloqueo[]
}

/** Cuerpo del alta: sin `profesional_id` ni `sillon_id` bloquea todo el consultorio. */
export interface NuevoBloqueo {
  inicio: string
  fin: string
  motivo: string
  profesional_id?: number
  sillon_id?: number
}

const RUTA = '/api/bloqueos'
const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor.'
const ALCANCES = ['profesional', 'sillon', 'consultorio']

function esObjeto(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === 'object' && valor !== null
}

function esIdONulo(valor: unknown): valor is number | null {
  return valor === null || typeof valor === 'number'
}

function esSillon(valor: unknown): valor is Sillon {
  return (
    esObjeto(valor) &&
    typeof valor.id === 'number' &&
    typeof valor.nombre === 'string' &&
    typeof valor.activo === 'boolean'
  )
}

function esBloqueo(valor: unknown): valor is Bloqueo {
  return (
    esObjeto(valor) &&
    typeof valor.id === 'number' &&
    typeof valor.alcance === 'string' &&
    ALCANCES.includes(valor.alcance) &&
    esIdONulo(valor.profesional_id) &&
    esIdONulo(valor.sillon_id) &&
    typeof valor.inicio === 'string' &&
    typeof valor.fin === 'string' &&
    typeof valor.motivo === 'string' &&
    typeof valor.creado_por === 'number'
  )
}

function esTurnoAfectado(valor: unknown): valor is TurnoAfectado {
  return (
    esObjeto(valor) &&
    typeof valor.id === 'number' &&
    typeof valor.inicio === 'string' &&
    typeof valor.fin === 'string' &&
    typeof valor.estado === 'string' &&
    typeof valor.profesional_id === 'number' &&
    typeof valor.sillon_id === 'number' &&
    typeof valor.paciente_id === 'number'
  )
}

function esBloqueoCreado(valor: unknown): valor is BloqueoCreado {
  return (
    esBloqueo(valor) &&
    'turnos_afectados' in valor &&
    Array.isArray(valor.turnos_afectados) &&
    valor.turnos_afectados.every(esTurnoAfectado)
  )
}

function esLista(valor: unknown): valor is BloqueosDelConsultorio {
  return (
    esObjeto(valor) &&
    typeof valor.zona_horaria === 'string' &&
    Array.isArray(valor.bloqueos) &&
    valor.bloqueos.every(esBloqueo)
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

export interface ApiBloqueos {
  listarBloqueos(): Promise<BloqueosDelConsultorio>
  crearBloqueo(nuevo: NuevoBloqueo): Promise<BloqueoCreado>
  eliminarBloqueo(id: number): Promise<void>
  listarSillones(): Promise<Sillon[]>
}

export function crearApiBloqueos(pedidoDelPanel: PedidoDelPanel): ApiBloqueos {
  return {
    async listarBloqueos() {
      const cuerpo = await leerJson(await pedidoDelPanel(RUTA))
      if (!esLista(cuerpo)) throw new SinConexion(MENSAJE_SIN_CONEXION, null)
      return cuerpo
    },
    async crearBloqueo(nuevo) {
      const init: RequestInit = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(nuevo),
      }
      const cuerpo = await leerJson(await pedidoDelPanel(RUTA, init))
      if (!esBloqueoCreado(cuerpo)) throw new SinConexion(MENSAJE_SIN_CONEXION, null)
      return cuerpo
    },
    async eliminarBloqueo(id) {
      const respuesta = await pedidoDelPanel(`${RUTA}/${id}`, { method: 'DELETE' })
      if (!respuesta.ok) throw await traducirRechazo(respuesta)
      if (respuesta.status !== 204) throw new SinConexion(MENSAJE_SIN_CONEXION, null)
    },
    async listarSillones() {
      const cuerpo = await leerJson(await pedidoDelPanel('/api/sillones'))
      if (!Array.isArray(cuerpo) || !cuerpo.every(esSillon)) throw new SinConexion(MENSAJE_SIN_CONEXION, null)
      return cuerpo
    },
  }
}
