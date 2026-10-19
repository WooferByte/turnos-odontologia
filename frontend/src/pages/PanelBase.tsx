// Diseño común del panel (design F11, D225, T2): encabezado con la navegación y el cierre de sesión,
// ningún dato del usuario, y debajo la pantalla elegida por la ruta.
import { NavLink, Outlet, useNavigate } from 'react-router'
import { useSesionDelPanel } from '../shared/api/ProveedorDeSesion'

export function PanelBase() {
  const { cerrarSesion } = useSesionDelPanel()
  const navegar = useNavigate()

  function cerrar(): void {
    cerrarSesion()
    navegar('/ingresar', { replace: true })
  }

  return (
    <div className="panel">
      <header className="encabezado">
        <strong className="marca">Turnos Odontológicos AR</strong>
        <nav aria-label="Principal">
          <NavLink to="/panel/prestaciones" className="enlace-del-panel">
            Prestaciones
          </NavLink>
        </nav>
        <button type="button" className="boton-secundario" onClick={cerrar}>
          Cerrar sesión
        </button>
      </header>
      <main className="contenido">
        <Outlet />
      </main>
    </div>
  )
}
