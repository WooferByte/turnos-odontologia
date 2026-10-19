// Panel lateral de alta y edición (design T9, T10, T17). Recibe los errores ya traducidos a mensajes y no
// valida reglas de dominio: la duración la decide la API (D232).
import { useId, useState, type SyntheticEvent } from 'react'
import { IconoAlerta } from '../../shared/iconos/IconoAlerta'
import { IconoCerrar } from '../../shared/iconos/IconoCerrar'
import { IconoInfo } from '../../shared/iconos/IconoInfo'
import { IconoLapiz } from '../../shared/iconos/IconoLapiz'
import { IconoMas } from '../../shared/iconos/IconoMas'
import type { DatosDeAlta, Prestacion } from './apiPrestaciones'
import { Aviso } from './Aviso'
import { MENSAJE_AVISO_DE_DURACION, subtituloDelPanel, type ErroresDelPanel } from './mensajes'

const COLOR_INICIAL = '#1E88E5'

interface Propiedades {
  /** La prestación que se edita; `null` abre el alta. */
  prestacion: Prestacion | null
  guardando: boolean
  errores: ErroresDelPanel
  onGuardar(datos: DatosDeAlta): void
  onCancelar(): void
}

export function PanelDePrestacion({ prestacion, guardando, errores, onGuardar, onCancelar }: Propiedades) {
  const idTitulo = useId()
  const idNombre = useId()
  const idDuracion = useId()
  const idAyuda = useId()
  const idAvisoDeTurnos = useId()
  const idErrorNombre = useId()
  const idErrorDuracion = useId()
  const idColor = useId()
  const idReserva = useId()
  const [nombre, setNombre] = useState(prestacion?.nombre ?? '')
  const [duracion, setDuracion] = useState(prestacion === null ? '' : String(prestacion.duracion_minutos))
  // El control nativo entrega y acepta el hex en minúsculas; la API recibe mayúsculas (D233).
  const [color, setColor] = useState((prestacion?.color ?? COLOR_INICIAL).toLowerCase())
  const [reservaOnline, setReservaOnline] = useState(prestacion?.reservable_online ?? false)

  function guardar(evento: SyntheticEvent<HTMLFormElement>): void {
    evento.preventDefault()
    // Un color sin tocar se manda tal como lo guardó la API, para que no cuente como cambio.
    const colorSinTocar = prestacion !== null && color === prestacion.color.toLowerCase()
    onGuardar({
      nombre,
      duracion_minutos: Number(duracion),
      color: colorSinTocar ? prestacion.color : color.toUpperCase(),
      reservable_online: reservaOnline,
    })
  }

  const descripciones = [idAyuda, prestacion === null ? null : idAvisoDeTurnos, errores.duracion === null ? null : idErrorDuracion]

  return (
    <aside aria-labelledby={idTitulo} className="panel-lateral">
      <header className="panel-encabezado">
        <div>
          <h2 id={idTitulo}>
            {prestacion === null ? <IconoMas /> : <IconoLapiz />}
            {prestacion === null ? 'Nueva prestación' : 'Editar prestación'}
          </h2>
          <p className="panel-subtitulo">{subtituloDelPanel(prestacion)}</p>
        </div>
        <button type="button" className="boton-cerrar" aria-label="Cerrar" onClick={onCancelar}>
          <IconoCerrar />
        </button>
      </header>
      <div className="panel-cuerpo">
        {errores.aviso === null ? null : <Aviso mensaje={errores.aviso} />}
        <form onSubmit={guardar}>
          <div className={errores.nombre === null ? 'campo' : 'campo campo-con-error'}>
            <div className="campo-etiqueta">
              <label htmlFor={idNombre} className="etiqueta-obligatoria">
                Nombre
              </label>
            </div>
            <div className="entrada-con-icono">
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
              {errores.nombre === null ? null : <IconoAlerta clase="icono icono-en-campo" />}
            </div>
            {errores.nombre === null ? null : (
              <p id={idErrorNombre} className="error-de-campo">
                {errores.nombre}
              </p>
            )}
          </div>
          <div className={errores.duracion === null ? 'campo' : 'campo campo-con-error'}>
            <div className="campo-etiqueta">
              <label htmlFor={idDuracion} className="etiqueta-obligatoria">
                Duración en minutos
              </label>
              <p id={idAyuda} className="ayuda">
                Mayor que 0 y múltiplo de 5.
              </p>
            </div>
            <div className="entrada-con-icono">
              <input
                id={idDuracion}
                type="number"
                required
                step="1"
                value={duracion}
                onChange={(e) => setDuracion(e.target.value)}
                aria-invalid={errores.duracion === null ? undefined : true}
                aria-describedby={descripciones.filter((id) => id !== null).join(' ')}
              />
              {errores.duracion === null ? null : <IconoAlerta clase="icono icono-en-campo" />}
            </div>
            {errores.duracion === null ? null : (
              <p id={idErrorDuracion} className="error-de-campo">
                {errores.duracion}
              </p>
            )}
            {prestacion === null ? null : (
              <p id={idAvisoDeTurnos} className="nota-informativa">
                <IconoInfo />
                {MENSAJE_AVISO_DE_DURACION}
              </p>
            )}
          </div>
          <div className="campo">
            <div className="campo-etiqueta">
              <label htmlFor={idColor}>Color</label>
            </div>
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
          <div className="panel-pie">
            <button type="button" className="boton-secundario" onClick={onCancelar}>
              Cancelar
            </button>
            <button type="submit" className="boton-primario" disabled={guardando}>
              {guardando ? 'Guardando…' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </aside>
  )
}
