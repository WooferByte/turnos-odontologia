// Panel lateral de alta y edición (design T9, T10). Recibe los errores ya traducidos a mensajes y no
// valida reglas de dominio: la duración la decide la API (D232).
import { useId, useState, type SyntheticEvent } from 'react'
import type { DatosDeAlta } from './apiPrestaciones'
import type { ErroresDelPanel } from './mensajes'

const COLOR_INICIAL = '#1E88E5'

interface Propiedades {
  guardando: boolean
  errores: ErroresDelPanel
  onGuardar(datos: DatosDeAlta): void
  onCancelar(): void
}

export function PanelDePrestacion({ guardando, errores, onGuardar, onCancelar }: Propiedades) {
  const idTitulo = useId()
  const idNombre = useId()
  const idDuracion = useId()
  const idAyuda = useId()
  const idErrorNombre = useId()
  const idErrorDuracion = useId()
  const idColor = useId()
  const idReserva = useId()
  const [nombre, setNombre] = useState('')
  const [duracion, setDuracion] = useState('')
  const [color, setColor] = useState(COLOR_INICIAL.toLowerCase())
  const [reservaOnline, setReservaOnline] = useState(false)

  function guardar(evento: SyntheticEvent<HTMLFormElement>): void {
    evento.preventDefault()
    onGuardar({
      nombre,
      duracion_minutos: Number(duracion),
      color: color.toUpperCase(),
      reservable_online: reservaOnline,
    })
  }

  return (
    <aside aria-labelledby={idTitulo} className="panel-lateral">
      <h2 id={idTitulo}>Nueva prestación</h2>
      {errores.aviso === null ? null : (
        <div role="alert" className="aviso aviso-error">
          {errores.aviso}
        </div>
      )}
      <form onSubmit={guardar}>
        <div className="campo">
          <label htmlFor={idNombre}>Nombre</label>
          <input
            id={idNombre}
            type="text"
            required
            autoFocus
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            aria-invalid={errores.nombre === null ? undefined : true}
            aria-describedby={errores.nombre === null ? undefined : idErrorNombre}
          />
          {errores.nombre === null ? null : (
            <p id={idErrorNombre} className="error-de-campo">
              {errores.nombre}
            </p>
          )}
        </div>
        <div className="campo">
          <label htmlFor={idDuracion}>Duración en minutos</label>
          <input
            id={idDuracion}
            type="number"
            required
            step="1"
            value={duracion}
            onChange={(e) => setDuracion(e.target.value)}
            aria-invalid={errores.duracion === null ? undefined : true}
            aria-describedby={errores.duracion === null ? idAyuda : `${idAyuda} ${idErrorDuracion}`}
          />
          <p id={idAyuda} className="ayuda">
            Mayor que 0 y múltiplo de 5.
          </p>
          {errores.duracion === null ? null : (
            <p id={idErrorDuracion} className="error-de-campo">
              {errores.duracion}
            </p>
          )}
        </div>
        <div className="campo">
          <label htmlFor={idColor}>Color</label>
          <div className="selector-de-color">
            <input id={idColor} type="color" value={color} onChange={(e) => setColor(e.target.value)} />
            <output htmlFor={idColor}>{color.toUpperCase()}</output>
          </div>
        </div>
        <div className="campo campo-casilla">
          <input
            id={idReserva}
            type="checkbox"
            checked={reservaOnline}
            onChange={(e) => setReservaOnline(e.target.checked)}
          />
          <label htmlFor={idReserva}>Ofrecer en la reserva online</label>
        </div>
        <div className="acciones-del-panel">
          <button type="submit" className="boton-primario" disabled={guardando}>
            {guardando ? 'Guardando…' : 'Guardar'}
          </button>
          <button type="button" className="boton-secundario" onClick={onCancelar}>
            Cancelar
          </button>
        </div>
      </form>
    </aside>
  )
}
