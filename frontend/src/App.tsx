// Rutas de la interfaz (design F6). El `fetch` se inyecta solo en los tests.
import { Navigate, Route, Routes } from 'react-router'
import { PaginaIngreso } from './features/ingreso/PaginaIngreso'
import { PanelBase } from './pages/PanelBase'
import type { Fetch } from './shared/api/clienteHttp'
import { ProveedorDeSesion } from './shared/api/ProveedorDeSesion'

interface Propiedades {
  fetch?: Fetch
}

export function App({ fetch }: Propiedades) {
  return (
    <ProveedorDeSesion {...(fetch === undefined ? {} : { fetch })}>
      <Routes>
        <Route path="/ingresar" element={<PaginaIngreso />} />
        <Route path="/panel/*" element={<PanelBase />} />
        <Route path="*" element={<Navigate to="/panel" replace />} />
      </Routes>
    </ProveedorDeSesion>
  )
}
