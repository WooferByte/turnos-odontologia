// Tabla de usuarios (design U17): activos e inactivos en el orden de la API. Lo inactivo se atenúa y lleva la
// insignia «Inactivo», así el estado no depende solo del color. No hay acción de borrar (RN-GL-03).
import type { Usuario } from './apiUsuarios'
import { nombreDelRol } from './mensajes'

interface Propiedades {
  usuarios: readonly Usuario[]
  /** Ids con una acción de fila esperando respuesta: sus botones quedan deshabilitados. */
  ocupadas: ReadonlySet<number>
  /** Id del usuario que el panel lateral está editando, si hay uno. */
  editandoId: number | null
  onEditar(usuario: Usuario): void
  onCambiarActivo(usuario: Usuario): void
}

function claseDeFila(usuario: Usuario, editando: boolean): string {
  return ['fila', usuario.activo ? null : 'fila-inactiva', editando ? 'fila-editando' : null]
    .filter((clase) => clase !== null)
    .join(' ')
}

export function TablaDeUsuarios({ usuarios, ocupadas, editandoId, onEditar, onCambiarActivo }: Propiedades) {
  return (
    <table className="tabla tabla-de-usuarios">
      <thead>
        <tr>
          <th scope="col">Email</th>
          <th scope="col">Roles</th>
          <th scope="col">Estado</th>
          <th scope="col">Acciones</th>
        </tr>
      </thead>
      <tbody>
        {usuarios.map((usuario) => {
          const accion = usuario.activo ? 'Desactivar' : 'Reactivar'
          const ocupada = ocupadas.has(usuario.id)
          return (
            <tr key={usuario.id} className={claseDeFila(usuario, usuario.id === editandoId)}>
              <td>
                {usuario.email}
                {usuario.id === editandoId ? (
                  <>
                    {' '}
                    <span className="marca-editando">Editando</span>
                  </>
                ) : null}
              </td>
              <td>
                <ul className="roles-del-usuario">
                  {usuario.roles.map((rol) => (
                    <li key={rol} className="insignia-de-rol">
                      {nombreDelRol(rol)}
                    </li>
                  ))}
                </ul>
              </td>
              <td>
                <span className={usuario.activo ? 'insignia insignia-activa' : 'insignia insignia-inactiva'}>
                  {usuario.activo ? 'Activo' : 'Inactivo'}
                </span>
              </td>
              <td className="acciones-de-fila">
                <button
                  type="button"
                  className={usuario.id === editandoId ? 'boton-de-fila boton-de-fila-en-edicion' : 'boton-de-fila'}
                  disabled={ocupada}
                  aria-label={`Editar ${usuario.email}`}
                  onClick={() => onEditar(usuario)}
                >
                  Editar
                </button>
                <button
                  type="button"
                  className={usuario.activo ? 'boton-de-fila boton-de-fila-peligro' : 'boton-de-fila boton-de-fila-exito'}
                  disabled={ocupada}
                  aria-label={`${accion} ${usuario.email}`}
                  onClick={() => onCambiarActivo(usuario)}
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
