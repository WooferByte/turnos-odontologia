// Diseño común del panel (design F11, D225, T2, T17): barra superior con la marca, la navegación, el usuario
// de la sesión (C-50) y el cierre de sesión, y debajo la pantalla elegida por la ruta.
import { NavLink, Outlet, useNavigate } from 'react-router'
import { IndicadorDeSesion } from '../features/sesion/IndicadorDeSesion'
import { useSesionDelPanel } from '../shared/api/ProveedorDeSesion'
import { IconoCalendario } from '../shared/iconos/IconoCalendario'
import { IconoLlave } from '../shared/iconos/IconoLlave'
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
            <NavLink to="/panel/bloqueos" className="enlace-del-panel">
              <IconoCalendario />
              Bloqueos
            </NavLink>
            <NavLink to="/panel/contrasena" className="enlace-del-panel">
              <IconoLlave />
              Mi contraseña
            </NavLink>
          </nav>
          <IndicadorDeSesion />
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
