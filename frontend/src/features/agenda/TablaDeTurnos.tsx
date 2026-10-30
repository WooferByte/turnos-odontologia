// Tabla de la agenda del día (design A9, A14, G2): una fila por turno en el orden de la API, con la columna
// «Acciones» (botones «Asistencia» (solo reservado y confirmado), «Reprogramar» y «Cancelar» (solo en los turnos activos) e «Historial»). Debajo de 720 px cada fila se acomoda como tarjeta (solo CSS). El color de la
// prestación es un dato de la API: va como `style` en línea.
import type { CSSProperties } from 'react'
import { horaLocal } from '../../shared/horaDelConsultorio'
import { IconoAsistencia } from '../../shared/iconos/IconoAsistencia'
import { IconoCancelar } from '../../shared/iconos/IconoCancelar'
import { IconoCalendario } from '../../shared/iconos/IconoCalendario'
import { IconoReloj } from '../../shared/iconos/IconoReloj'
import { ESTADOS_ACTIVOS_DEL_TURNO, ESTADOS_QUE_SE_MARCAN_DEL_TURNO, type TurnoDeLaAgenda } from './apiAgenda'
import { ETIQUETAS_DE_ESTADO, TONOS_DE_ESTADO } from './mensajes'

interface Propiedades {
  turnos: readonly TurnoDeLaAgenda[]
  zonaHoraria: string
  /** El turno cuyo panel (historial, reprogramar o cancelar) está abierto, para marcar su fila; `null` si no hay. */
  turnoSeleccionadoId: number | null
  onRegistrarAsistencia(turno: TurnoDeLaAgenda): void
  onReprogramar(turno: TurnoDeLaAgenda): void
  onCancelar(turno: TurnoDeLaAgenda): void
  onVerHistorial(turno: TurnoDeLaAgenda): void
}

function estiloDeFila(color: string): CSSProperties {
  return { '--color-de-prestacion': color } as CSSProperties
}

export function TablaDeTurnos({
  turnos,
  zonaHoraria,
  turnoSeleccionadoId,
  onRegistrarAsistencia,
  onReprogramar,
  onCancelar,
  onVerHistorial,
}: Propiedades) {
  return (
    <table className="tabla tabla-de-agenda" aria-label="Turnos del día">
      <thead>
        <tr>
          <th scope="col">Hora</th>
          <th scope="col">Paciente</th>
          <th scope="col">Prestación</th>
          <th scope="col">Estado</th>
          <th scope="col">Acciones</th>
        </tr>
      </thead>
      <tbody>
        {turnos.map((turno) => (
          <tr
            key={turno.id}
            className={turno.id === turnoSeleccionadoId ? 'fila-de-turno fila-seleccionada' : 'fila-de-turno'}
            style={estiloDeFila(turno.prestacion.color)}
          >
            <td className="cifras">
              {horaLocal(turno.inicio, zonaHoraria)} – {horaLocal(turno.fin, zonaHoraria)}
            </td>
            <td className="paciente-del-turno">
              {turno.paciente.nombre} {turno.paciente.apellido}
            </td>
            <td>
              <span
                className="marca-de-color"
                data-color={turno.prestacion.color}
                style={{ backgroundColor: turno.prestacion.color }}
              />
              {turno.prestacion.nombre}
            </td>
            <td>
              <span className={`chip-de-estado chip-${TONOS_DE_ESTADO[turno.estado]}`}>
                {ETIQUETAS_DE_ESTADO[turno.estado]}
              </span>
            </td>
            <td className="acciones-del-turno">
              {ESTADOS_QUE_SE_MARCAN_DEL_TURNO.includes(turno.estado) ? (
                <button
                  type="button"
                  className="boton-secundario boton-de-asistencia"
                  aria-label={`Registrar la asistencia del turno de ${turno.paciente.nombre} ${turno.paciente.apellido}, ${horaLocal(turno.inicio, zonaHoraria)}`}
                  data-asistencia-id={turno.id}
                  onClick={() => onRegistrarAsistencia(turno)}
                >
                  <IconoAsistencia />
                  Asistencia
                </button>
              ) : null}
              {ESTADOS_ACTIVOS_DEL_TURNO.includes(turno.estado) ? (
                <button
                  type="button"
                  className="boton-secundario boton-de-reprogramar"
                  aria-label={`Reprogramar el turno de ${turno.paciente.nombre} ${turno.paciente.apellido}, ${horaLocal(turno.inicio, zonaHoraria)}`}
                  data-reprogramar-id={turno.id}
                  onClick={() => onReprogramar(turno)}
                >
                  <IconoCalendario />
                  Reprogramar
                </button>
              ) : null}
              {ESTADOS_ACTIVOS_DEL_TURNO.includes(turno.estado) ? (
                <button
                  type="button"
                  className="boton-secundario boton-de-cancelar"
                  aria-label={`Cancelar el turno de ${turno.paciente.nombre} ${turno.paciente.apellido}, ${horaLocal(turno.inicio, zonaHoraria)}`}
                  data-cancelar-id={turno.id}
                  onClick={() => onCancelar(turno)}
                >
                  <IconoCancelar />
                  Cancelar
                </button>
              ) : null}
              <button
                type="button"
                className="boton-secundario boton-de-historial"
                aria-label={`Historial del turno de ${turno.paciente.nombre} ${turno.paciente.apellido}, ${horaLocal(turno.inicio, zonaHoraria)}`}
                data-turno-id={turno.id}
                onClick={() => onVerHistorial(turno)}
              >
                <IconoReloj />
                Historial
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
