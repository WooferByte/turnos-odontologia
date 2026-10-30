// Panel lateral «Registrar asistencia» (design W12, W13): pregunta cómo terminó el turno, sin opción marcada, y manda
// el estado elegido. No evalúa reglas: las decide la API (tampoco compara la hora del turno con el reloj).
import { useId, useState, type SyntheticEvent } from 'react'
import { Aviso } from '../../shared/componentes/Aviso'
import { fechaLocal, horaLocal } from '../../shared/horaDelConsultorio'
import { IconoAsistencia } from '../../shared/iconos/IconoAsistencia'
import { IconoCerrar } from '../../shared/iconos/IconoCerrar'
import { IconoInfo } from '../../shared/iconos/IconoInfo'
import type { EstadoDeAsistencia, TurnoDeLaAgenda } from './apiAgenda'
import {
  ACCION_REGISTRAR_ASISTENCIA,
  AYUDA_DE_CANCELACION,
  ETIQUETAS_DE_ESTADO,
  MENSAJE_ELEGI_COMO_TERMINO,
  MENSAJE_EL_TURNO_NO_CAMBIO,
  OPCION_ATENDIDO,
  OPCION_AUSENTE,
  PREGUNTA_DE_ASISTENCIA,
  nombreDelDia,
  tituloDelAviso,
} from './mensajes'

interface Propiedades {
  turno: TurnoDeLaAgenda
  zonaHoraria: string
  enviando: boolean
  /** Rechazo de la API ya traducido a su texto fijo; `null` si no hay. */
  error: string | null
  onRegistrar(estado: EstadoDeAsistencia): void
  /** Cierra el panel sin pedir nada («Volver» y «Cerrar»). */
  onVolver(): void
}

const OPCIONES: readonly { estado: EstadoDeAsistencia; texto: string }[] = [
  { estado: 'atendido', texto: OPCION_ATENDIDO },
  { estado: 'ausente', texto: OPCION_AUSENTE },
]

export function PanelAsistencia({ turno, zonaHoraria, enviando, error, onRegistrar, onVolver }: Propiedades) {
  const idTitulo = useId()
  const nombre = useId()
  const [elegido, setElegido] = useState<EstadoDeAsistencia | null>(null)
  /** Lo que la pantalla frena sin pedir nada a la API; elegir una opción lo quita. */
  const [frenado, setFrenado] = useState<string | null>(null)

  function registrar(evento: SyntheticEvent<HTMLFormElement>): void {
    evento.preventDefault()
    if (enviando) return
    if (elegido === null) {
      setFrenado(MENSAJE_ELEGI_COMO_TERMINO)
      return
    }
    onRegistrar(elegido)
  }

  return (
    <aside aria-labelledby={idTitulo} className="panel-lateral panel-de-turno panel-de-asistencia">
      <header className="panel-encabezado">
        <div>
          <h2 id={idTitulo}>
            <IconoAsistencia />
            {ACCION_REGISTRAR_ASISTENCIA}
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
        <form onSubmit={registrar} noValidate>
          <fieldset className="opciones-de-cancelacion">
            <legend>{PREGUNTA_DE_ASISTENCIA}</legend>
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
            <button type="submit" className="boton-primario" disabled={enviando}>
              {ACCION_REGISTRAR_ASISTENCIA}
            </button>
          </div>
        </form>
      </div>
    </aside>
  )
}
