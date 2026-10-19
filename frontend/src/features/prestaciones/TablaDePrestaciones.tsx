// Tabla del catálogo (design T8): activas e inactivas en el orden de la API. Lo inactivo se atenúa y lleva
// la insignia «Inactiva», así el estado no depende solo del color. No hay acción de borrar (RN-GL-03).
import type { Prestacion } from './apiPrestaciones'

interface Propiedades {
  prestaciones: readonly Prestacion[]
  /** Ids con una acción de fila esperando respuesta: sus botones quedan deshabilitados. */
  ocupadas: ReadonlySet<number>
  /** Id de la prestación que el panel lateral está editando, si hay una. */
  editandoId: number | null
  onEditar(prestacion: Prestacion): void
  onCambiarActiva(prestacion: Prestacion): void
}

function claseDeFila(prestacion: Prestacion, editando: boolean): string {
  return ['fila', prestacion.activa ? null : 'fila-inactiva', editando ? 'fila-editando' : null]
    .filter((clase) => clase !== null)
    .join(' ')
}

export function TablaDePrestaciones({ prestaciones, ocupadas, editandoId, onEditar, onCambiarActiva }: Propiedades) {
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
        {prestaciones.map((prestacion) => {
          const accion = prestacion.activa ? 'Desactivar' : 'Reactivar'
          const ocupada = ocupadas.has(prestacion.id)
          return (
            <tr key={prestacion.id} className={claseDeFila(prestacion, prestacion.id === editandoId)}>
              <td>
                <span
                  role="img"
                  aria-label={`Color ${prestacion.color}`}
                  className="muestra-de-color"
                  style={{ backgroundColor: prestacion.color }}
                />
              </td>
              <td>
                {prestacion.nombre}
                {prestacion.id === editandoId ? (
                  <>
                    {' '}
                    <span className="marca-editando">Editando</span>
                  </>
                ) : null}
              </td>
              <td className="cifras">{prestacion.duracion_minutos} min</td>
              <td>{prestacion.reservable_online ? 'Sí' : 'No'}</td>
              <td>
                <span className={prestacion.activa ? 'insignia insignia-activa' : 'insignia insignia-inactiva'}>
                  {prestacion.activa ? 'Activa' : 'Inactiva'}
                </span>
              </td>
              <td className="acciones-de-fila">
                <button
                  type="button"
                  className={prestacion.id === editandoId ? 'boton-de-fila boton-de-fila-en-edicion' : 'boton-de-fila'}
                  disabled={ocupada}
                  aria-label={`Editar ${prestacion.nombre}`}
                  onClick={() => onEditar(prestacion)}
                >
                  Editar
                </button>
                <button
                  type="button"
                  className={prestacion.activa ? 'boton-de-fila' : 'boton-de-fila boton-de-fila-primario'}
                  disabled={ocupada}
                  aria-label={`${accion} ${prestacion.nombre}`}
                  onClick={() => onCambiarActiva(prestacion)}
                >
                  {accion}
                </button>
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
