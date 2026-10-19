// Cliente de prestaciones (design T5): habla con `GET/POST/PATCH /api/prestaciones` a través de la
// función `pedidoDelPanel` que recibe (inyectada). No evalúa reglas: todo `4xx` pasa por `traducirRechazo`.
import type { PedidoDelPanel } from '../../shared/api/clienteHttp'
import { SinConexion } from '../../shared/api/errores'
import { traducirRechazo } from '../../shared/api/rechazos'

export interface Prestacion {
  id: number
  nombre: string
  duracion_minutos: number
  color: string
  reservable_online: boolean
  activa: boolean
}

export interface DatosDeAlta {
  nombre: string
  duracion_minutos: number
  color: string
  reservable_online: boolean
}

/** Solo los campos presentes se mandan (con `exactOptionalPropertyTypes` no hay `undefined`). */
export interface CambiosDePrestacion {
  nombre?: string
  duracion_minutos?: number
  color?: string
  reservable_online?: boolean
  activa?: boolean
}

const RUTA = '/api/prestaciones'
const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor.'

function esPrestacion(valor: unknown): valor is Prestacion {
  if (typeof valor !== 'object' || valor === null) return false
  const v = valor as Record<string, unknown>
  return (
    typeof v.id === 'number' &&
    typeof v.nombre === 'string' &&
    typeof v.duracion_minutos === 'number' &&
    typeof v.color === 'string' &&
    typeof v.reservable_online === 'boolean' &&
    typeof v.activa === 'boolean'
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

async function leerPrestacion(respuesta: Response): Promise<Prestacion> {
  const cuerpo = await leerJson(respuesta)
  if (!esPrestacion(cuerpo)) throw new SinConexion(MENSAJE_SIN_CONEXION, null)
  return cuerpo
}

function conCuerpo(metodo: string, cuerpo: object): RequestInit {
  return { method: metodo, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cuerpo) }
}

export interface ApiPrestaciones {
  listarPrestaciones(): Promise<Prestacion[]>
  crearPrestacion(datos: DatosDeAlta): Promise<Prestacion>
  editarPrestacion(id: number, cambios: CambiosDePrestacion): Promise<Prestacion>
}

export function crearApiPrestaciones(pedidoDelPanel: PedidoDelPanel): ApiPrestaciones {
  return {
    async listarPrestaciones() {
      const cuerpo = await leerJson(await pedidoDelPanel(RUTA))
      if (!Array.isArray(cuerpo) || !cuerpo.every(esPrestacion)) throw new SinConexion(MENSAJE_SIN_CONEXION, null)
      return cuerpo
    },
    async crearPrestacion(datos) {
      return leerPrestacion(await pedidoDelPanel(RUTA, conCuerpo('POST', datos)))
    },
    async editarPrestacion(id, cambios) {
      return leerPrestacion(await pedidoDelPanel(`${RUTA}/${id}`, conCuerpo('PATCH', cambios)))
    },
  }
}

/** Lo que cambió entre la prestación original y la editada. El nombre se compara tal cual (RN-AG-15 lo decide la API). */
export function cambiosEntre(original: Prestacion, editado: Omit<Prestacion, 'id'>): CambiosDePrestacion {
  const cambios: CambiosDePrestacion = {}
  if (editado.nombre !== original.nombre) cambios.nombre = editado.nombre
  if (editado.duracion_minutos !== original.duracion_minutos) cambios.duracion_minutos = editado.duracion_minutos
  if (editado.color !== original.color) cambios.color = editado.color
  if (editado.reservable_online !== original.reservable_online) cambios.reservable_online = editado.reservable_online
  if (editado.activa !== original.activa) cambios.activa = editado.activa
  return cambios
}
