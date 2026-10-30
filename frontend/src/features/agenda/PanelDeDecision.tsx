// Estructura común de «Cancelar turno» y «Registrar asistencia» (D234, design W12): el resumen del turno, una pregunta
// con dos opciones sin valor inicial, la ayuda y el pie con «Volver» y el botón de la decisión. No evalúa reglas: las
// decide la API.
import { useId, useState, type ReactNode, type SyntheticEvent } from 'react'
import { Aviso } from '../../shared/componentes/Aviso'
import { fechaLocal, horaLocal } from '../../shared/horaDelConsultorio'
import { IconoCerrar } from '../../shared/iconos/IconoCerrar'
import { IconoInfo } from '../../shared/iconos/IconoInfo'
import type { TurnoDeLaAgenda } from './apiAgenda'
import { ETIQUETAS_DE_ESTADO, MENSAJE_EL_TURNO_NO_CAMBIO, nombreDelDia, tituloDelAviso } from './mensajes'

export interface OpcionDeDecision<E extends string> {
  estado: E
  texto: string
}

interface Propiedades<E extends string> {
  /** Modificador de estilo del panel (`panel-de-cancelar`, `panel-de-asistencia`). */
  clase: string
  titulo: string
  icono: ReactNode
  turno: TurnoDeLaAgenda
  zonaHoraria: string
  pregunta: string
  opciones: readonly OpcionDeDecision<E>[]
  ayuda: string
  /** Lo que se muestra si se confirma sin elegir; la pantalla lo frena sin pedir nada a la API. */
  mensajeSinOpcion: string
  textoDelBoton: string
  claseDelBoton: string
  enviando: boolean
  /** Rechazo de la API ya traducido a su texto fijo; `null` si no hay. */
  error: string | null
  onConfirmar(estado: E): void
  /** Cierra el panel sin pedir nada («Volver» y «Cerrar»). */
  onVolver(): void
}

export function PanelDeDecision<E extends string>({
  clase,
  titulo,
  icono,
  turno,
  zonaHoraria,
  pregunta,
  opciones,
  ayuda,
  mensajeSinOpcion,
  textoDelBoton,
  claseDelBoton,
  enviando,
  error,
  onConfirmar,
  onVolver,
}: Propiedades<E>) {
  const idTitulo = useId()
  const nombre = useId()
  const [elegido, setElegido] = useState<E | null>(null)
  /** Lo que la pantalla frena sin pedir nada a la API; elegir una opción lo quita. */
  const [frenado, setFrenado] = useState<string | null>(null)

  function confirmar(evento: SyntheticEvent<HTMLFormElement>): void {
    evento.preventDefault()
    if (enviando) return
    if (elegido === null) {
      setFrenado(mensajeSinOpcion)
      return
    }
    onConfirmar(elegido)
  }

  return (
    <aside aria-labelledby={idTitulo} className={`panel-lateral panel-de-turno panel-de-decision ${clase}`}>
      <header className="panel-encabezado">
        <div>
          <h2 id={idTitulo}>
            {icono}
            {titulo}
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
        <form onSubmit={confirmar} noValidate>
          <fieldset className="opciones-de-decision">
            <legend>{pregunta}</legend>
            {opciones.map((opcion, i) => (
              <label key={opcion.estado} className="opcion-de-decision">
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
            {ayuda}
          </p>
          <div className="panel-pie">
            <button type="button" className="boton-secundario" onClick={onVolver}>
              Volver
            </button>
            <button type="submit" className={claseDelBoton} disabled={enviando}>
              {textoDelBoton}
            </button>
          </div>
        </form>
      </div>
    </aside>
  )
}
