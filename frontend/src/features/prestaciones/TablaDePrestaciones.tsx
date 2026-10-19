// Tabla del catálogo (design T8): activas e inactivas en el orden de la API. Lo inactivo se atenúa y lleva
// la insignia «Inactiva», así el estado no depende solo del color.
import type { Prestacion } from './apiPrestaciones'

interface Propiedades {
  prestaciones: readonly Prestacion[]
}

export function TablaDePrestaciones({ prestaciones }: Propiedades) {
  return (
    <table className="tabla">
      <thead>
        <tr>
          <th scope="col">Color</th>
          <th scope="col">Nombre</th>
          <th scope="col">Duración</th>
          <th scope="col">Reserva online</th>
          <th scope="col">Estado</th>
          <th scope="col">Acciones</th>
        </tr>
      </thead>
      <tbody>
        {prestaciones.map((prestacion) => (
          <tr key={prestacion.id} className={prestacion.activa ? 'fila' : 'fila fila-inactiva'}>
            <td>
              <span
                role="img"
                aria-label={`Color ${prestacion.color}`}
                className="muestra-de-color"
                style={{ backgroundColor: prestacion.color }}
              />
            </td>
            <td>{prestacion.nombre}</td>
            <td className="cifras">{prestacion.duracion_minutos} min</td>
            <td>{prestacion.reservable_online ? 'Sí' : 'No'}</td>
            <td>
              <span className={prestacion.activa ? 'insignia insignia-activa' : 'insignia insignia-inactiva'}>
                {prestacion.activa ? 'Activa' : 'Inactiva'}
              </span>
            </td>
            <td>
              <button
                type="button"
                className="boton-secundario"
                aria-label={`${prestacion.activa ? 'Desactivar' : 'Reactivar'} ${prestacion.nombre}`}
              >
                {prestacion.activa ? 'Desactivar' : 'Reactivar'}
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
