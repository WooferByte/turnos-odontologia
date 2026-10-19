// Única traducción de un 4xx del panel a un error de TypeScript (design T6). La interfaz no evalúa reglas:
// clasifica lo que la API respondió. Lee el cuerpo `application/problem+json` sin `any`.
import {
  EntradaRechazada,
  PermisoInsuficiente,
  ReglaRechazada,
  RecursoInexistente,
  SinConexion,
  type ErrorDeApi,
  type ErrorDeCampo,
} from './errores'

const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor.'

interface CuerpoDelProblema {
  codigos: string[]
  errores: ErrorDeCampo[]
}

function esObjeto(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === 'object' && valor !== null
}

function errorDeCampo(valor: unknown): ErrorDeCampo | null {
  if (!esObjeto(valor)) return null
  const { campo, codigo, mensaje } = valor
  if (campo !== null && typeof campo !== 'string') return null
  if (codigo !== null && typeof codigo !== 'string') return null
  if (typeof mensaje !== 'string') return null
  return { campo, codigo, mensaje }
}

async function leerProblema(respuesta: Response): Promise<CuerpoDelProblema> {
  try {
    const cuerpo: unknown = await respuesta.clone().json()
    if (!esObjeto(cuerpo)) return { codigos: [], errores: [] }
    const codigos = Array.isArray(cuerpo.codigos)
      ? cuerpo.codigos.filter((c: unknown): c is string => typeof c === 'string')
      : []
    const errores = Array.isArray(cuerpo.errores)
      ? cuerpo.errores.flatMap((e: unknown) => {
          const campo = errorDeCampo(e)
          return campo === null ? [] : [campo]
        })
      : []
    return { codigos, errores }
  } catch {
    return { codigos: [], errores: [] }
  }
}

export async function traducirRechazo(respuesta: Response): Promise<ErrorDeApi> {
  const { codigos, errores } = await leerProblema(respuesta)
  const codigo = codigos[0] ?? null
  switch (respuesta.status) {
    case 403:
      return new PermisoInsuficiente('Permiso insuficiente.', codigo)
    case 404:
      return new RecursoInexistente('Recurso inexistente.', codigo)
    case 409:
      return new ReglaRechazada('Regla de negocio rechazada.', codigo)
    case 422:
      return new EntradaRechazada('Entrada rechazada.', codigo, codigos, errores)
    default:
      return new SinConexion(MENSAJE_SIN_CONEXION, null)
  }
}
