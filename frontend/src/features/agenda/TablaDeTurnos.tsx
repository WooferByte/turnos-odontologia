// Tabla de la agenda del día (design A9, A14): una fila por turno en el orden de la API. Debajo de 720 px cada
// fila se acomoda como tarjeta (solo CSS). El color de la prestación es un dato de la API: va como `style` en línea.
import type { CSSProperties } from 'react'
import { horaLocal } from '../../shared/horaDelConsultorio'
import type { TurnoDeLaAgenda } from './apiAgenda'
import { ETIQUETAS_DE_ESTADO, TONOS_DE_ESTADO } from './mensajes'

interface Propiedades {
  turnos: readonly TurnoDeLaAgenda[]
  zonaHoraria: string
}

function estiloDeFila(color: string): CSSProperties {
  return { '--color-de-prestacion': color } as CSSProperties
}

export function TablaDeTurnos({ turnos, zonaHoraria }: Propiedades) {
  return (
    <table className="tabla tabla-de-agenda" aria-label="Turnos del día">
      <thead>
        <tr>
          <th scope="col">Hora</th>
          <th scope="col">Paciente</th>
          <th scope="col">Prestación</th>
          <th scope="col">Estado</th>
        </tr>
      </thead>
      <tbody>
        {turnos.map((turno) => (
          <tr key={turno.id} className="fila-de-turno" style={estiloDeFila(turno.prestacion.color)}>
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
          </tr>
        ))}
      </tbody>
    </table>
  )
}
