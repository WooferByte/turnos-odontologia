// Cliente de contraseñas (design K13): habla con `POST /api/usuarios/{id}/restablecer-contrasena` y
// `POST /api/auth/cambiar-contrasena` a través de `pedidoDelPanel` (inyectado). No evalúa reglas: todo
// `4xx` pasa por `traducirRechazo`. Ninguna contraseña se guarda ni se registra aquí.
import type { PedidoDelPanel } from '../../shared/api/clienteHttp'
import { SinConexion } from '../../shared/api/errores'
import { traducirRechazo } from '../../shared/api/rechazos'

export interface TokensNuevos {
  access: string
  refresh: string
}

export interface ApiContrasenas {
  /** `204` sin cuerpo: la fila del usuario no cambia. */
  restablecerContrasena(usuarioId: number, contrasena: string): Promise<void>
  /** `200` con los tokens que reemplazan a los de la sesión actual (D291). */
  cambiarContrasena(contrasenaActual: string, contrasenaNueva: string): Promise<TokensNuevos>
}

const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor.'

function conCuerpo(cuerpo: object): RequestInit {
  return { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cuerpo) }
}

async function leerTokens(respuesta: Response): Promise<TokensNuevos> {
  if (!respuesta.ok) throw await traducirRechazo(respuesta)
  try {
    const cuerpo: unknown = await respuesta.json()
    if (
      typeof cuerpo === 'object' &&
      cuerpo !== null &&
      'access_token' in cuerpo &&
      typeof cuerpo.access_token === 'string' &&
      'refresh_token' in cuerpo &&
      typeof cuerpo.refresh_token === 'string'
    ) {
      return { access: cuerpo.access_token, refresh: cuerpo.refresh_token }
    }
  } catch {
    // Cuerpo ilegible: se trata como falla de transporte.
  }
  throw new SinConexion(MENSAJE_SIN_CONEXION, null)
}

export function crearApiContrasenas(pedidoDelPanel: PedidoDelPanel): ApiContrasenas {
  return {
    async restablecerContrasena(usuarioId, contrasena) {
      const respuesta = await pedidoDelPanel(
        `/api/usuarios/${usuarioId}/restablecer-contrasena`,
        conCuerpo({ contrasena }),
      )
      if (!respuesta.ok) throw await traducirRechazo(respuesta)
    },
    async cambiarContrasena(contrasenaActual, contrasenaNueva) {
      const respuesta = await pedidoDelPanel(
        '/api/auth/cambiar-contrasena',
        conCuerpo({ contrasena_actual: contrasenaActual, contrasena_nueva: contrasenaNueva }),
      )
      return leerTokens(respuesta)
    },
  }
}
