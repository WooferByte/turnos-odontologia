// Cliente del historial de un turno (design G8): habla con `GET /api/turnos/{id}/historial` a través de la función
// `pedidoDelPanel` que recibe (inyectada). No evalúa reglas: todo `4xx` pasa por `traducirRechazo` y la respuesta
// `2xx` se valida sin `any`; una respuesta de otra forma es `SinConexion`.
import type { PedidoDelPanel } from '../../shared/api/clienteHttp'
import { SinConexion } from '../../shared/api/errores'
import { traducirRechazo } from '../../shared/api/rechazos'

export interface EventoDelHistorial {
  id: number
  turno_id: number
  tipo: string
  actor_tipo: string
  /** El id del usuario como texto; `null` si no se identificó (D159). */
  actor_id: string | null
  /** ISO en UTC con `Z`. */
  ocurrido_en: string
  antes: Record<string, unknown> | null
  despues: Record<string, unknown> | null
  motivo: string | null
}

const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor.'

function esObjeto(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === 'object' && valor !== null
}

function esTextoONulo(valor: unknown): valor is string | null {
  return valor === null || typeof valor === 'string'
}

function esObjetoONulo(valor: unknown): valor is Record<string, unknown> | null {
  return valor === null || esObjeto(valor)
}

function esEvento(valor: unknown): valor is EventoDelHistorial {
  return (
    esObjeto(valor) &&
    typeof valor.id === 'number' &&
    typeof valor.turno_id === 'number' &&
    typeof valor.tipo === 'string' &&
    typeof valor.actor_tipo === 'string' &&
    esTextoONulo(valor.actor_id) &&
    typeof valor.ocurrido_en === 'string' &&
    esObjetoONulo(valor.antes) &&
    esObjetoONulo(valor.despues) &&
    esTextoONulo(valor.motivo)
  )
}

function sonEventos(valor: unknown): valor is EventoDelHistorial[] {
  return Array.isArray(valor) && valor.every(esEvento)
}

export interface ApiHistorial {
  /** Los eventos del turno en el orden de la API (RN-AG-11); la pantalla no los reordena. */
  obtenerHistorial(turnoId: number): Promise<EventoDelHistorial[]>
}

export function crearApiHistorial(pedidoDelPanel: PedidoDelPanel): ApiHistorial {
  return {
    async obtenerHistorial(turnoId) {
      const respuesta = await pedidoDelPanel(`/api/turnos/${turnoId}/historial`)
      if (!respuesta.ok) throw await traducirRechazo(respuesta)
      let cuerpo: unknown
      try {
        cuerpo = await respuesta.json()
      } catch {
        throw new SinConexion(MENSAJE_SIN_CONEXION, null)
      }
      if (!sonEventos(cuerpo)) throw new SinConexion(MENSAJE_SIN_CONEXION, null)
      return cuerpo
    },
  }
}
