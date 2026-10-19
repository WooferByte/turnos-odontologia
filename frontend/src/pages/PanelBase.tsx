// Panel base (design F11, D225): encabezado con el cierre de sesión y ningún dato del usuario.
import { useNavigate } from 'react-router'
import { useSesionDelPanel } from '../shared/api/ProveedorDeSesion'

export function PanelBase() {
  const { cerrarSesion } = useSesionDelPanel()
  const navegar = useNavigate()

  function cerrar(): void {
    cerrarSesion()
    navegar('/ingresar', { replace: true })
  }

  return (
    <div>
      <header>
        <strong>Turnos Odontológicos AR</strong>
        <button type="button" onClick={cerrar}>
          Cerrar sesión
        </button>
      </header>
      <main>
        <h1>Panel del consultorio</h1>
      </main>
    </div>
  )
}
