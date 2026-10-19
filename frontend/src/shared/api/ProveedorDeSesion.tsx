// Proveedor de sesión del panel (design F10): estado de la sesión para el árbol de React.
import { createContext, useContext, useState, type ReactNode } from 'react'
import { crearClienteHttp, type Fetch } from './clienteHttp'
import { crearSesion } from './sesion'

export type EstadoDeSesion = 'verificando' | 'con-sesion' | 'sin-sesion'
export type AvisoDeSesion = 'sesion-terminada' | 'sin-conexion' | null

export interface ContextoDeSesion {
  estado: EstadoDeSesion
  aviso: AvisoDeSesion
  iniciarSesion(email: string, contrasena: string): Promise<void>
  cerrarSesion(): void
}

const Contexto = createContext<ContextoDeSesion | null>(null)

export function useSesionDelPanel(): ContextoDeSesion {
  const contexto = useContext(Contexto)
  if (contexto === null) throw new Error('useSesionDelPanel se usa dentro de ProveedorDeSesion')
  return contexto
}

interface Propiedades {
  fetch?: Fetch
  children: ReactNode
}

export function ProveedorDeSesion({ fetch, children }: Propiedades) {
  const [infraestructura] = useState(() => {
    const sesion = crearSesion()
    const cliente = crearClienteHttp(fetch === undefined ? { sesion } : { fetch, sesion })
    return { sesion, cliente }
  })
  const [estado, setEstado] = useState<EstadoDeSesion>('sin-sesion')
  const [aviso, setAviso] = useState<AvisoDeSesion>(null)

  async function iniciarSesion(email: string, contrasena: string): Promise<void> {
    await infraestructura.cliente.iniciarSesion(email, contrasena)
    setEstado('con-sesion')
    setAviso(null)
  }

  function cerrarSesion(): void {
    infraestructura.sesion.borrar()
    setEstado('sin-sesion')
    setAviso(null)
  }

  return <Contexto value={{ estado, aviso, iniciarSesion, cerrarSesion }}>{children}</Contexto>
}
