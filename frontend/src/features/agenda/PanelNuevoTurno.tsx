// Panel lateral «Nuevo turno» (design A10, A11, A13): pide paciente (por número hasta C-20), prestación, fecha y hora
// del consultorio. No valida reglas: solo exige que estén los campos; el profesional y el sillón los resuelve la API.
import { useId, useState, type SyntheticEvent } from 'react'
import { Aviso } from '../../shared/componentes/Aviso'
import { IconoCerrar } from '../../shared/iconos/IconoCerrar'
import { IconoMas } from '../../shared/iconos/IconoMas'
import { aUtc, horaLocal } from '../../shared/horaDelConsultorio'
import type { Prestacion } from '../prestaciones/apiPrestaciones'
import type { NuevoTurno } from './apiAgenda'
import { MENSAJE_FORMULARIO_INCOMPLETO, textoDeFin, tituloDelAviso } from './mensajes'

interface Propiedades {
  /** Las prestaciones activas; `null` mientras llegan. */
  prestaciones: readonly Prestacion[] | null
  /** El día mostrado (`aaaa-mm-dd`), con el que arranca «Fecha». */
  fechaInicial: string
  zonaHoraria: string
  enviando: boolean
  /** Rechazo de la API ya traducido a su texto fijo; `null` si no hay. */
  error: string | null
  onCrear(nuevo: NuevoTurno): void
  onCancelar(): void
}

const NUMERO_DE_PACIENTE = /^\d+$/
const FECHA = /^\d{4}-\d{2}-\d{2}$/
const HORA = /^\d{2}:\d{2}$/

/** `hh:mm` en que termina un turno que empieza en `fecha` y `hora` del consultorio, o `null` si falta algo. */
function horaDeFin(fecha: string, hora: string, duracionMinutos: number, zona: string): string | null {
  if (!FECHA.test(fecha) || !HORA.test(hora)) return null
  const fin = new Date(Date.parse(aUtc(`${fecha}T${hora}`, zona)) + duracionMinutos * 60000)
  return horaLocal(fin.toISOString(), zona)
}

export function PanelNuevoTurno({
  prestaciones,
  fechaInicial,
  zonaHoraria,
  enviando,
  error,
  onCrear,
  onCancelar,
}: Propiedades) {
  const idTitulo = useId()
  const idPaciente = useId()
  const idAyudaPaciente = useId()
  const idPrestacion = useId()
  const idFecha = useId()
  const idHora = useId()
  const idFin = useId()
  const [paciente, setPaciente] = useState('')
  const [prestacionId, setPrestacionId] = useState('')
  const [fecha, setFecha] = useState(fechaInicial)
  const [hora, setHora] = useState('')
  const [incompleto, setIncompleto] = useState(false)

  const elegida = prestaciones?.find((p) => String(p.id) === prestacionId)
  // Una prestación que ya no está entre las activas se ve como «sin elegir» (derivado, no guardado).
  const prestacionVista = elegida === undefined ? '' : prestacionId
  const fin = elegida === undefined ? null : horaDeFin(fecha, hora, elegida.duracion_minutos, zonaHoraria)
  const mensaje = incompleto ? MENSAJE_FORMULARIO_INCOMPLETO : error

  function cambiar(cambio: () => void): void {
    cambio()
    setIncompleto(false)
  }

  function crear(evento: SyntheticEvent<HTMLFormElement>): void {
    evento.preventDefault()
    if (enviando) return
    if (!NUMERO_DE_PACIENTE.test(paciente.trim()) || elegida === undefined || !FECHA.test(fecha) || !HORA.test(hora)) {
      setIncompleto(true)
      return
    }
    onCrear({
      paciente_id: Number(paciente.trim()),
      prestacion_id: elegida.id,
      inicio: aUtc(`${fecha}T${hora}`, zonaHoraria),
    })
  }

  return (
    <aside aria-labelledby={idTitulo} className="panel-lateral panel-de-turno">
      <header className="panel-encabezado">
        <div>
          <h2 id={idTitulo}>
            <IconoMas />
            Nuevo turno
          </h2>
          <p className="panel-subtitulo">Fecha y hora del consultorio.</p>
        </div>
        <button type="button" className="boton-cerrar" aria-label="Cerrar" onClick={onCancelar}>
          <IconoCerrar />
        </button>
      </header>
      <div className="panel-cuerpo">
        {mensaje === null ? null : <Aviso mensaje={mensaje} titulo={tituloDelAviso(mensaje)} />}
        <form onSubmit={crear} noValidate>
          <div className="campo">
            <div className="campo-etiqueta">
              <label htmlFor={idPaciente} className="etiqueta-obligatoria">
                N.º de paciente
              </label>
              <p id={idAyudaPaciente} className="ayuda">
                El número de ficha del paciente.
              </p>
            </div>
            <input
              id={idPaciente}
              type="text"
              inputMode="numeric"
              autoFocus
              autoComplete="off"
              value={paciente}
              onChange={(e) => cambiar(() => setPaciente(e.target.value))}
              aria-describedby={idAyudaPaciente}
            />
          </div>
          <div className="campo">
            <div className="campo-etiqueta">
              <label htmlFor={idPrestacion} className="etiqueta-obligatoria">
                Prestación
              </label>
            </div>
            <select
              id={idPrestacion}
              value={prestacionVista}
              onChange={(e) => cambiar(() => setPrestacionId(e.target.value))}
            >
              <option value="">{prestaciones === null ? 'Cargando prestaciones…' : 'Elegí una prestación'}</option>
              {(prestaciones ?? []).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre} · {p.duracion_minutos} min
                </option>
              ))}
            </select>
          </div>
          <div className="campos-en-fila">
            <div className="campo">
              <div className="campo-etiqueta">
                <label htmlFor={idFecha} className="etiqueta-obligatoria">
                  Fecha
                </label>
              </div>
              <input id={idFecha} type="date" value={fecha} onChange={(e) => cambiar(() => setFecha(e.target.value))} />
            </div>
            <div className="campo">
              <div className="campo-etiqueta">
                <label htmlFor={idHora} className="etiqueta-obligatoria">
                  Hora
                </label>
              </div>
              <input
                id={idHora}
                type="time"
                value={hora}
                onChange={(e) => cambiar(() => setHora(e.target.value))}
                aria-describedby={fin === null ? undefined : idFin}
              />
            </div>
          </div>
          {fin === null ? null : (
            <p id={idFin} className="ayuda">
              {textoDeFin(fin)}
            </p>
          )}
          <div className="panel-pie">
            <button type="button" className="boton-secundario" onClick={onCancelar}>
              Cancelar
            </button>
            <button type="submit" className="boton-primario" disabled={enviando}>
              Crear turno
            </button>
          </div>
        </form>
      </div>
    </aside>
  )
}
