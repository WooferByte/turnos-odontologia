// Proveedor de sesión del panel (design F10): estado de la sesión para el árbol de React.
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { crearClienteHttp, type Fetch, type PedidoDelPanel } from './clienteHttp'
import { SesionTerminada } from './errores'
import { crearSesion } from './sesion'

export type EstadoDeSesion = 'verificando' | 'con-sesion' | 'sin-sesion'
export type AvisoDeSesion = 'sesion-terminada' | 'sin-conexion' | null

export interface ContextoDeSesion {
  estado: EstadoDeSesion
  aviso: AvisoDeSesion
  iniciarSesion(email: string, contrasena: string): Promise<void>
  cerrarSesion(): void
  /** Pedido a una ruta del panel: si la sesión termina, pasa a `sin-sesion` con el aviso y relanza el error (design T4). */
  pedidoDelPanel: PedidoDelPanel
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
  const [estado, setEstado] = useState<EstadoDeSesion>(() =>
    infraestructura.sesion.refresh() === null ? 'sin-sesion' : 'verificando',
  )
  const [aviso, setAviso] = useState<AvisoDeSesion>(null)

  // Arranque (F10): con un refresh guardado se renueva el access antes de mostrar nada del panel.
  useEffect(() => {
    if (estado !== 'verificando') return
    let vigente = true
    infraestructura.cliente.renovarSesion().then(
      () => {
        if (vigente) setEstado('con-sesion')
      },
      (error: unknown) => {
        if (!vigente) return
        setEstado('sin-sesion')
        setAviso(error instanceof SesionTerminada ? 'sesion-terminada' : 'sin-conexion')
      },
    )
    return () => {
      vigente = false
    }
  }, [estado, infraestructura])

  async function iniciarSesion(email: string, contrasena: string): Promise<void> {
    setAviso(null)
    await infraestructura.cliente.iniciarSesion(email, contrasena)
    setEstado('con-sesion')
  }

  function cerrarSesion(): void {
    infraestructura.sesion.borrar()
    setEstado('sin-sesion')
    setAviso(null)
  }

  const pedidoDelPanel = useCallback<PedidoDelPanel>(
    async (ruta, opciones) => {
      try {
        return await infraestructura.cliente.pedidoDelPanel(ruta, opciones)
      } catch (error) {
        if (error instanceof SesionTerminada) {
          setEstado('sin-sesion')
          setAviso('sesion-terminada')
        }
        throw error
      }
    },
    [infraestructura],
  )

  return <Contexto value={{ estado, aviso, iniciarSesion, cerrarSesion, pedidoDelPanel }}>{children}</Contexto>
}
