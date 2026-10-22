// Tabla de usuarios (design U17): activos e inactivos en el orden de la API. Lo inactivo se atenúa y lleva la
// insignia «Inactivo», así el estado no depende solo del color. No hay acción de borrar (RN-GL-03).
import type { Usuario } from './apiUsuarios'
import { nombreDelRol } from './mensajes'

interface Propiedades {
  usuarios: readonly Usuario[]
}

function claseDeFila(usuario: Usuario): string {
  return usuario.activo ? 'fila' : 'fila fila-inactiva'
}

export function TablaDeUsuarios({ usuarios }: Propiedades) {
  return (
    <table className="tabla">
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
          return (
            <tr key={usuario.id} className={claseDeFila(usuario)}>
              <td>{usuario.email}</td>
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
                <button type="button" className="boton-de-fila" aria-label={`Editar ${usuario.email}`}>
                  Editar
                </button>
                <button
                  type="button"
                  className={usuario.activo ? 'boton-de-fila' : 'boton-de-fila boton-de-fila-primario'}
                  aria-label={`${accion} ${usuario.email}`}
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
