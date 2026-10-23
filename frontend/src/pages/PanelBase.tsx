// Diseño común del panel (design F11, D225, T2, T17): barra superior con la marca, la navegación y el
// cierre de sesión, ningún dato del usuario, y debajo la pantalla elegida por la ruta.
import { NavLink, Outlet, useNavigate } from 'react-router'
import { useSesionDelPanel } from '../shared/api/ProveedorDeSesion'
import { IconoDiente } from '../shared/iconos/IconoDiente'
import { IconoMaletin } from '../shared/iconos/IconoMaletin'
import { IconoReloj } from '../shared/iconos/IconoReloj'
import { IconoSalida } from '../shared/iconos/IconoSalida'
import { IconoUsuarios } from '../shared/iconos/IconoUsuarios'

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
        <div className="encabezado-interior">
          <strong className="marca">
            <IconoDiente clase="icono icono-marca" />
            Turnos Odontológicos AR
          </strong>
          <nav aria-label="Principal">
            <NavLink to="/panel/prestaciones" className="enlace-del-panel">
              <IconoMaletin />
              Prestaciones
            </NavLink>
            <NavLink to="/panel/usuarios" className="enlace-del-panel">
              <IconoUsuarios />
              Usuarios
            </NavLink>
            <NavLink to="/panel/horario" className="enlace-del-panel">
              <IconoReloj />
              Horario
            </NavLink>
          </nav>
          <button type="button" className="boton-secundario" onClick={cerrar}>
            <IconoSalida />
            Cerrar sesión
          </button>
        </div>
      </header>
      <main className="contenido">
        <Outlet />
      </main>
    </div>
  )
}
