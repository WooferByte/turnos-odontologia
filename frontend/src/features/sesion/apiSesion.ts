// Cliente del usuario de la sesión (design Y8): habla con `GET /api/auth/yo` a través de `pedidoDelPanel`
// (inyectado). Un `401` lo resuelve `pedidoDelPanel` (renueva una vez; si no, `SesionTerminada`); una falla de
// red o un `5xx` salen como `SinConexion`. El `403` y un `200` de otra forma devuelven `null` (D310).
import type { PedidoDelPanel } from '../../shared/api/clienteHttp'
import { esRol, type Rol } from '../../shared/roles'

export interface UsuarioDeLaSesion {
  email: string
  roles: Rol[]
}

function esUsuarioDeLaSesion(valor: unknown): valor is UsuarioDeLaSesion {
  if (typeof valor !== 'object' || valor === null) return false
  const v = valor as Record<string, unknown>
  return typeof v.email === 'string' && Array.isArray(v.roles) && v.roles.every(esRol)
}

export async function obtenerUsuarioDeLaSesion(pedidoDelPanel: PedidoDelPanel): Promise<UsuarioDeLaSesion | null> {
  const respuesta = await pedidoDelPanel('/api/auth/yo')
  if (!respuesta.ok) return null
  try {
    const cuerpo: unknown = await respuesta.json()
    return esUsuarioDeLaSesion(cuerpo) ? { email: cuerpo.email, roles: cuerpo.roles } : null
  } catch {
    return null
  }
}
