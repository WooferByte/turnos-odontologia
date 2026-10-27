// Cliente de usuarios (design U18): habla con `GET/POST/PATCH /api/usuarios` a través de la función
// `pedidoDelPanel` que recibe (inyectada). No evalúa reglas: todo `4xx` pasa por `traducirRechazo`.
import type { PedidoDelPanel } from '../../shared/api/clienteHttp'
import { SinConexion } from '../../shared/api/errores'
import { traducirRechazo } from '../../shared/api/rechazos'
import { ROLES, esRol, type Rol } from '../../shared/roles'

export interface Usuario {
  id: number
  email: string
  roles: Rol[]
  activo: boolean
}

export interface DatosDeAltaDeUsuario {
  email: string
  contrasena: string
  roles: Rol[]
}

/** Solo los campos presentes se mandan (con `exactOptionalPropertyTypes` no hay `undefined`). */
export interface CambiosDeUsuario {
  roles?: Rol[]
  activo?: boolean
}

const RUTA = '/api/usuarios'
const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor.'

function esUsuario(valor: unknown): valor is Usuario {
  if (typeof valor !== 'object' || valor === null) return false
  const v = valor as Record<string, unknown>
  return (
    typeof v.id === 'number' &&
    typeof v.email === 'string' &&
    Array.isArray(v.roles) &&
    v.roles.every(esRol) &&
    typeof v.activo === 'boolean'
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

async function leerUsuario(respuesta: Response): Promise<Usuario> {
  const cuerpo = await leerJson(respuesta)
  if (!esUsuario(cuerpo)) throw new SinConexion(MENSAJE_SIN_CONEXION, null)
  return cuerpo
}

function conCuerpo(metodo: string, cuerpo: object): RequestInit {
  return { method: metodo, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cuerpo) }
}

export interface ApiUsuarios {
  listarUsuarios(): Promise<Usuario[]>
  crearUsuario(datos: DatosDeAltaDeUsuario): Promise<Usuario>
  editarUsuario(id: number, cambios: CambiosDeUsuario): Promise<Usuario>
}

export function crearApiUsuarios(pedidoDelPanel: PedidoDelPanel): ApiUsuarios {
  return {
    async listarUsuarios() {
      const cuerpo = await leerJson(await pedidoDelPanel(RUTA))
      if (!Array.isArray(cuerpo) || !cuerpo.every(esUsuario)) throw new SinConexion(MENSAJE_SIN_CONEXION, null)
      return cuerpo
    },
    async crearUsuario(datos) {
      return leerUsuario(await pedidoDelPanel(RUTA, conCuerpo('POST', datos)))
    },
    async editarUsuario(id, cambios) {
      return leerUsuario(await pedidoDelPanel(`${RUTA}/${id}`, conCuerpo('PATCH', cambios)))
    },
  }
}

/** ¿Los roles marcados son distintos de los originales? Compara conjuntos: el orden no cuenta. */
export function rolesCambiados(original: readonly Rol[], marcados: readonly Rol[]): boolean {
  const antes = new Set(original)
  const despues = new Set(marcados)
  return antes.size !== despues.size || [...despues].some((rol) => !antes.has(rol))
}
