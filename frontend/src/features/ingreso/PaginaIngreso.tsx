// Pantalla de inicio de sesión (design F9). Los mensajes son fijos de la interfaz: no se muestra el
// `detail` de la API, y los dos rechazos del login (RN-AU-04) se ven idénticos.
import { useState, type FormEvent } from 'react'
import { Navigate, useLocation } from 'react-router'
import { CredencialesRechazadas, EntradaRechazada } from '../../shared/api/errores'
import { useSesionDelPanel } from '../../shared/api/ProveedorDeSesion'

type Problema = 'credenciales' | 'entrada' | 'conexion'

const MENSAJES: Record<Problema, string> = {
  credenciales: 'El email o la contraseña no son correctos.',
  entrada: 'Revisá el email y la contraseña.',
  conexion: 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.',
}

function problemaDe(error: unknown): Problema {
  if (error instanceof CredencialesRechazadas) return 'credenciales'
  if (error instanceof EntradaRechazada) return 'entrada'
  return 'conexion'
}

const MENSAJE_SESION_TERMINADA = 'Tu sesión terminó. Iniciá sesión de nuevo.'
const RUTA_DEL_PANEL = /^\/panel(\/|\?|$)/

/** Solo se vuelve a una ruta del panel: nunca a una dirección arbitraria (F6). */
function destinoPedido(estadoDeNavegacion: unknown): string {
  if (typeof estadoDeNavegacion === 'object' && estadoDeNavegacion !== null && 'desde' in estadoDeNavegacion) {
    const { desde } = estadoDeNavegacion
    if (typeof desde === 'string' && RUTA_DEL_PANEL.test(desde)) return desde
  }
  return '/panel'
}

export function PaginaIngreso() {
  const { estado, aviso, iniciarSesion } = useSesionDelPanel()
  const ubicacion = useLocation()
  const [email, setEmail] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [problema, setProblema] = useState<Problema | null>(null)

  if (estado === 'con-sesion') return <Navigate to={destinoPedido(ubicacion.state)} replace />
  const problemaVisible = problema ?? (aviso === 'sin-conexion' ? 'conexion' : null)

  async function enviar(evento: FormEvent<HTMLFormElement>): Promise<void> {
    evento.preventDefault()
    setEnviando(true)
    setProblema(null)
    try {
      await iniciarSesion(email, contrasena)
    } catch (error) {
      const nuevo = problemaDe(error)
      if (nuevo !== 'conexion') setContrasena('')
      setProblema(nuevo)
      setEnviando(false)
    }
  }

  return (
    <main>
      <h1>Turnos Odontológicos AR</h1>
      <form method="post" onSubmit={(evento) => void enviar(evento)}>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="username"
          required
          value={email}
          onChange={(evento) => setEmail(evento.target.value)}
        />
        <label htmlFor="contrasena">Contraseña</label>
        <input
          id="contrasena"
          name="contrasena"
          type="password"
          autoComplete="current-password"
          required
          value={contrasena}
          onChange={(evento) => setContrasena(evento.target.value)}
        />
        {aviso === 'sesion-terminada' ? <p role="status">{MENSAJE_SESION_TERMINADA}</p> : null}
        {problemaVisible === null ? null : <p role="alert">{MENSAJES[problemaVisible]}</p>}
        <button type="submit" disabled={enviando}>
          {enviando ? 'Ingresando…' : 'Ingresar'}
        </button>
      </form>
    </main>
  )
}
