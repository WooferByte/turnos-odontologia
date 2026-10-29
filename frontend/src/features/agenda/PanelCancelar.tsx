// Panel lateral «Cancelar turno» (design X10, X11): pregunta quién pidió la cancelación, sin opción marcada, y manda
// el estado elegido. No evalúa reglas: las decide la API.
import { useId, useState, type SyntheticEvent } from 'react'
import { Aviso } from '../../shared/componentes/Aviso'
import { fechaLocal, horaLocal } from '../../shared/horaDelConsultorio'
import { IconoCancelar } from '../../shared/iconos/IconoCancelar'
import { IconoCerrar } from '../../shared/iconos/IconoCerrar'
import { IconoInfo } from '../../shared/iconos/IconoInfo'
import type { EstadoDeCancelacion, TurnoDeLaAgenda } from './apiAgenda'
import {
  AYUDA_DE_CANCELACION,
  ETIQUETAS_DE_ESTADO,
  MENSAJE_ELEGI_QUIEN_PIDIO,
  MENSAJE_EL_TURNO_NO_CAMBIO,
  OPCION_EL_CONSULTORIO,
  OPCION_EL_PACIENTE,
  PREGUNTA_DE_CANCELACION,
  nombreDelDia,
  tituloDelAviso,
} from './mensajes'

interface Propiedades {
  turno: TurnoDeLaAgenda
  zonaHoraria: string
  enviando: boolean
  /** Rechazo de la API ya traducido a su texto fijo; `null` si no hay. */
  error: string | null
  onCancelarTurno(estado: EstadoDeCancelacion): void
  /** Cierra el panel sin pedir nada («Volver» y «Cerrar»). */
  onVolver(): void
}

const OPCIONES: readonly { estado: EstadoDeCancelacion; texto: string }[] = [
  { estado: 'cancelado_paciente', texto: OPCION_EL_PACIENTE },
  { estado: 'cancelado_profesional', texto: OPCION_EL_CONSULTORIO },
]

export function PanelCancelar({ turno, zonaHoraria, enviando, error, onCancelarTurno, onVolver }: Propiedades) {
  const idTitulo = useId()
  const nombre = useId()
  const [elegido, setElegido] = useState<EstadoDeCancelacion | null>(null)
  /** Lo que la pantalla frena sin pedir nada a la API; elegir una opción lo quita. */
  const [frenado, setFrenado] = useState<string | null>(null)

  function cancelar(evento: SyntheticEvent<HTMLFormElement>): void {
    evento.preventDefault()
    if (enviando) return
    if (elegido === null) {
      setFrenado(MENSAJE_ELEGI_QUIEN_PIDIO)
      return
    }
    onCancelarTurno(elegido)
  }

  return (
    <aside aria-labelledby={idTitulo} className="panel-lateral panel-de-turno panel-de-cancelar">
      <header className="panel-encabezado">
        <div>
          <h2 id={idTitulo}>
            <IconoCancelar />
            Cancelar turno
          </h2>
          <p className="panel-subtitulo">
            {turno.paciente.nombre} {turno.paciente.apellido} · {turno.prestacion.nombre}
          </p>
          <p className="panel-subtitulo">
            {nombreDelDia(fechaLocal(turno.inicio, zonaHoraria))}, {horaLocal(turno.inicio, zonaHoraria)} –{' '}
            {horaLocal(turno.fin, zonaHoraria)} · {ETIQUETAS_DE_ESTADO[turno.estado]}
          </p>
        </div>
        <button type="button" className="boton-cerrar" aria-label="Cerrar" onClick={onVolver}>
          <IconoCerrar />
        </button>
      </header>
      <div className="panel-cuerpo">
        {frenado === null ? null : <Aviso mensaje={frenado} titulo={tituloDelAviso(frenado)} />}
        {frenado !== null || error === null ? null : (
          <Aviso mensaje={error} titulo={tituloDelAviso(error)}>
            <p className="aviso-segunda-linea">{MENSAJE_EL_TURNO_NO_CAMBIO}</p>
          </Aviso>
        )}
        <form onSubmit={cancelar} noValidate>
          <fieldset className="opciones-de-cancelacion">
            <legend>{PREGUNTA_DE_CANCELACION}</legend>
            {OPCIONES.map((opcion, i) => (
              <label key={opcion.estado} className="opcion-de-cancelacion">
                <input
                  type="radio"
                  name={nombre}
                  autoFocus={i === 0}
                  checked={elegido === opcion.estado}
                  onChange={() => {
                    setElegido(opcion.estado)
                    setFrenado(null)
                  }}
                />
                {opcion.texto}
              </label>
            ))}
          </fieldset>
          <p className="ayuda ayuda-con-icono">
            <IconoInfo clase="icono" />
            {AYUDA_DE_CANCELACION}
          </p>
          <div className="panel-pie">
            <button type="button" className="boton-secundario" onClick={onVolver}>
              Volver
            </button>
            <button type="submit" className="boton-destructivo" disabled={enviando}>
              Cancelar turno
            </button>
          </div>
        </form>
      </div>
    </aside>
  )
}
