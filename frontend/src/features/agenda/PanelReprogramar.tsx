// Panel lateral «Reprogramar turno» (design M10, M11, M12): pide fecha, hora y duración del consultorio, cargadas
// con los valores actuales del turno. No evalúa reglas de agenda: las decide la API.
import { useId, useState, type SyntheticEvent } from 'react'
import { Aviso } from '../../shared/componentes/Aviso'
import { aUtc, fechaLocal, horaLocal } from '../../shared/horaDelConsultorio'
import { IconoCalendario } from '../../shared/iconos/IconoCalendario'
import { IconoCerrar } from '../../shared/iconos/IconoCerrar'
import type { ReprogramacionDeTurno, TurnoDeLaAgenda } from './apiAgenda'
import { FECHA, HORA, horaDeFin } from './horaDeFin'
import {
  MENSAJE_EL_TURNO_NO_CAMBIO,
  MENSAJE_REPROGRAMACION_INCOMPLETA,
  MENSAJE_SIN_CAMBIOS,
  nombreDelDia,
  textoDeFin,
  tituloDelAviso,
} from './mensajes'

interface Propiedades {
  turno: TurnoDeLaAgenda
  zonaHoraria: string
  enviando: boolean
  /** Rechazo de la API ya traducido a su texto fijo; `null` si no hay. */
  error: string | null
  onReprogramar(cambio: ReprogramacionDeTurno): void
  onCancelar(): void
}

const NUMERO_ENTERO = /^\d+$/

export function PanelReprogramar({ turno, zonaHoraria, enviando, error, onReprogramar, onCancelar }: Propiedades) {
  const idTitulo = useId()
  const idFecha = useId()
  const idHora = useId()
  const idDuracion = useId()
  const idFin = useId()
  const fechaActual = fechaLocal(turno.inicio, zonaHoraria)
  const horaActual = horaLocal(turno.inicio, zonaHoraria)
  const [fecha, setFecha] = useState(fechaActual)
  const [hora, setHora] = useState(horaActual)
  const [duracion, setDuracion] = useState(String(turno.duracion_minutos))
  /** Lo que la pantalla frena sin pedir nada a la API (design M10); cualquier cambio de un campo lo quita. */
  const [frenado, setFrenado] = useState<string | null>(null)

  const fin = NUMERO_ENTERO.test(duracion.trim()) ? horaDeFin(fecha, hora, Number(duracion.trim()), zonaHoraria) : null

  function cambiar(cambio: () => void): void {
    cambio()
    setFrenado(null)
  }

  function reprogramar(evento: SyntheticEvent<HTMLFormElement>): void {
    evento.preventDefault()
    if (enviando) return
    if (!FECHA.test(fecha) || !HORA.test(hora) || !NUMERO_ENTERO.test(duracion.trim())) {
      setFrenado(MENSAJE_REPROGRAMACION_INCOMPLETA)
      return
    }
    const inicio = aUtc(`${fecha}T${hora}`, zonaHoraria)
    const duracionMinutos = Number(duracion.trim())
    if (Date.parse(inicio) === Date.parse(turno.inicio) && duracionMinutos === turno.duracion_minutos) {
      setFrenado(MENSAJE_SIN_CAMBIOS)
      return
    }
    onReprogramar({ inicio, duracion_minutos: duracionMinutos })
  }

  return (
    <aside aria-labelledby={idTitulo} className="panel-lateral panel-de-turno panel-de-reprogramar">
      <header className="panel-encabezado">
        <div>
          <h2 id={idTitulo}>
            <IconoCalendario />
            Reprogramar turno
          </h2>
          <p className="panel-subtitulo">
            {turno.paciente.nombre} {turno.paciente.apellido} · {turno.prestacion.nombre}
          </p>
          <p className="panel-subtitulo">
            Ahora: {nombreDelDia(fechaActual)}, {horaActual} – {horaLocal(turno.fin, zonaHoraria)}
          </p>
        </div>
        <button type="button" className="boton-cerrar" aria-label="Cerrar" onClick={onCancelar}>
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
        <p className="nota-del-panel">Fecha y hora del consultorio.</p>
        <form onSubmit={reprogramar} noValidate>
          <div className="campos-en-fila">
            <div className="campo">
              <div className="campo-etiqueta">
                <label htmlFor={idFecha} className="etiqueta-obligatoria">
                  Fecha
                </label>
              </div>
              <input id={idFecha} type="date" autoFocus value={fecha} onChange={(e) => cambiar(() => setFecha(e.target.value))} />
            </div>
            <div className="campo">
              <div className="campo-etiqueta">
                <label htmlFor={idHora} className="etiqueta-obligatoria">
                  Hora
                </label>
              </div>
              <input id={idHora} type="time" value={hora} onChange={(e) => cambiar(() => setHora(e.target.value))} />
            </div>
          </div>
          <div className="campo">
            <div className="campo-etiqueta">
              <label htmlFor={idDuracion} className="etiqueta-obligatoria">
                Duración (minutos)
              </label>
            </div>
            <input
              id={idDuracion}
              type="text"
              inputMode="numeric"
              autoComplete="off"
              value={duracion}
              onChange={(e) => cambiar(() => setDuracion(e.target.value))}
              aria-describedby={fin === null ? undefined : idFin}
            />
          </div>
          <div className="ayudas-de-duracion">
            <p className="ayuda">Múltiplo de 5 minutos.</p>
            {fin === null ? null : (
              <p id={idFin} className="ayuda">
                {textoDeFin(fin)}
              </p>
            )}
          </div>
          <div className="panel-pie">
            <button type="button" className="boton-secundario" onClick={onCancelar}>
              Cancelar
            </button>
            <button type="submit" className="boton-primario" disabled={enviando}>
              Reprogramar
            </button>
          </div>
        </form>
      </div>
    </aside>
  )
}
