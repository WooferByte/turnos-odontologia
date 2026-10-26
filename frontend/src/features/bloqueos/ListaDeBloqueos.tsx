// Bloqueos cargados (design B14, B16): una fila por bloqueo en el orden de la API, con «Eliminar» sin confirmación.
import { IconoPapelera } from '../../shared/iconos/IconoPapelera'
import type { Profesional } from '../horario/apiHorario'
import type { Bloqueo, Sillon } from './apiBloqueos'
import { aLocal } from './horaDelConsultorio'
import { etiquetaDelAlcance } from './mensajes'

interface Propiedades {
  bloqueos: readonly Bloqueo[]
  zonaHoraria: string
  profesionales: readonly Profesional[]
  sillones: readonly Sillon[]
  /** Id del bloqueo cuyo `DELETE` está esperando respuesta; su «Eliminar» queda deshabilitado. */
  eliminando: number | null
  onEliminar(id: number): void
}

export function ListaDeBloqueos({ bloqueos, zonaHoraria, profesionales, sillones, eliminando, onEliminar }: Propiedades) {
  return (
    <table className="tabla tabla-de-bloqueos">
      <thead>
        <tr>
          <th scope="col">Alcance</th>
          <th scope="col">Desde</th>
          <th scope="col">Hasta</th>
          <th scope="col">Motivo</th>
          <th scope="col">Acciones</th>
        </tr>
      </thead>
      <tbody>
        {bloqueos.map((bloqueo) => (
          <tr key={bloqueo.id}>
            <td>{etiquetaDelAlcance(bloqueo, profesionales, sillones)}</td>
            <td className="cifras">{aLocal(bloqueo.inicio, zonaHoraria)}</td>
            <td className="cifras">{aLocal(bloqueo.fin, zonaHoraria)}</td>
            <td>{bloqueo.motivo}</td>
            <td className="acciones-de-fila">
              <button
                type="button"
                className="boton-de-fila boton-de-fila-peligro"
                aria-label="Eliminar bloqueo"
                disabled={eliminando === bloqueo.id}
                onClick={() => onEliminar(bloqueo.id)}
              >
                <IconoPapelera />
                Eliminar
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
