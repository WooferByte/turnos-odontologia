// Aviso del `201` y los turnos activos que quedaron dentro del bloqueo (US-003 CA-2, D83, B16): se muestran
// sin cancelarlos y sin datos del paciente (D275).
import { IconoCheck } from '../../shared/iconos/IconoCheck'
import type { TurnoAfectado } from './apiBloqueos'
import { avisoDeCreado, filaDeTurnoAfectado } from './mensajes'

interface Propiedades {
  turnos: readonly TurnoAfectado[]
  zonaHoraria: string
}

export function TurnosAfectados({ turnos, zonaHoraria }: Propiedades) {
  return (
    <div role="status" className="aviso-exito aviso-de-creado">
      <p className="aviso-de-creado-mensaje">
        <IconoCheck clase="icono icono-exito" />
        {avisoDeCreado(turnos.length)}
      </p>
      {turnos.length > 0 ? (
        <ul className="turnos-afectados">
          {turnos.map((turno) => (
            <li key={turno.id}>
              <span>{filaDeTurnoAfectado(turno, zonaHoraria)}</span>
              <span className="etiqueta-de-estado">{turno.estado}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
