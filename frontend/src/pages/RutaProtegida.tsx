// Ruta protegida (design F10): nunca muestra el panel sin una sesión confirmada.
import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router'
import { useSesionDelPanel } from '../shared/api/ProveedorDeSesion'

interface Propiedades {
  children: ReactNode
}

export function RutaProtegida({ children }: Propiedades) {
  const { estado } = useSesionDelPanel()
  const ubicacion = useLocation()

  if (estado === 'verificando') return <p className="pantalla-de-ingreso">Cargando…</p>
  if (estado === 'sin-sesion') {
    return <Navigate to="/ingresar" replace state={{ desde: ubicacion.pathname + ubicacion.search }} />
  }
  return children
}
