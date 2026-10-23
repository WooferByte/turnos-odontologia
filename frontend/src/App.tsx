// Rutas de la interfaz (design F6, T2). El `fetch` se inyecta solo en los tests.
import { Navigate, Route, Routes } from 'react-router'
import { PaginaIngreso } from './features/ingreso/PaginaIngreso'
import { PaginaHorario } from './features/horario/PaginaHorario'
import { PaginaPrestaciones } from './features/prestaciones/PaginaPrestaciones'
import { PaginaUsuarios } from './features/usuarios/PaginaUsuarios'
import { InicioDelPanel } from './pages/InicioDelPanel'
import { PanelBase } from './pages/PanelBase'
import { RutaProtegida } from './pages/RutaProtegida'
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
        <Route
          path="/panel"
          element={
            <RutaProtegida>
              <PanelBase />
            </RutaProtegida>
          }
        >
          <Route index element={<InicioDelPanel />} />
          <Route path="prestaciones" element={<PaginaPrestaciones />} />
          <Route path="usuarios" element={<PaginaUsuarios />} />
          <Route path="horario" element={<PaginaHorario />} />
          <Route path="*" element={<InicioDelPanel />} />
        </Route>
        <Route path="*" element={<Navigate to="/panel" replace />} />
      </Routes>
    </ProveedorDeSesion>
  )
}
