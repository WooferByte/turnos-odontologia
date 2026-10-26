// Panel lateral de alta y edición de usuarios (design U18, U19). Recibe los errores ya traducidos a mensajes y no
// valida reglas: el formato del email, el largo de la contraseña y los roles los decide la API (D232, D242).
// La contraseña vive solo en el estado de este formulario y se descarta al desmontarse el panel.
import { useId, useState, type SyntheticEvent } from 'react'
import { Aviso } from '../../shared/componentes/Aviso'
import { IconoAlerta } from '../../shared/iconos/IconoAlerta'
import { IconoCerrar } from '../../shared/iconos/IconoCerrar'
import { IconoInfo } from '../../shared/iconos/IconoInfo'
import { IconoLlave } from '../../shared/iconos/IconoLlave'
import { IconoLapiz } from '../../shared/iconos/IconoLapiz'
import { IconoPersonaMas } from '../../shared/iconos/IconoPersonaMas'
import { AYUDA_DE_LARGO, NOTA_DE_RESTABLECER } from '../contrasenas/mensajes'
import { ROLES, type DatosDeAltaDeUsuario, type Rol, type Usuario } from './apiUsuarios'
import { NOTA_DE_ROLES, nombreDelRol, subtituloDelPanel, tituloDelAviso, type ErroresDelPanel } from './mensajes'

interface Propiedades {
  /** El usuario cuyos roles se editan; `null` abre el alta. */
  usuario: Usuario | null
  guardando: boolean
  errores: ErroresDelPanel
  onGuardar(datos: DatosDeAltaDeUsuario): void
  onCancelar(): void
}

export function PanelDeUsuario({ usuario, guardando, errores, onGuardar, onCancelar }: Propiedades) {
  const idTitulo = useId()
  const idEmail = useId()
  const idContrasena = useId()
  const idAyuda = useId()
  const idErrorEmail = useId()
  const idErrorContrasena = useId()
  const idErrorRoles = useId()
  const [email, setEmail] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [marcados, setMarcados] = useState<ReadonlySet<Rol>>(new Set(usuario?.roles ?? []))

  function alternar(rol: Rol, marcado: boolean): void {
    setMarcados((anteriores) => {
      const siguientes = new Set(anteriores)
      if (marcado) siguientes.add(rol)
      else siguientes.delete(rol)
      return siguientes
    })
  }

  function guardar(evento: SyntheticEvent<HTMLFormElement>): void {
    evento.preventDefault()
    onGuardar({ email, contrasena, roles: ROLES.filter((rol) => marcados.has(rol)) })
  }

  return (
    <aside aria-labelledby={idTitulo} className="panel-lateral panel-de-usuario">
      <header className="panel-encabezado">
        <div>
          <h2 id={idTitulo}>
            {usuario === null ? <IconoPersonaMas /> : <IconoLapiz />}
            {usuario === null ? 'Nuevo usuario' : 'Editar usuario'}
          </h2>
          <p className="panel-subtitulo">{subtituloDelPanel(usuario)}</p>
        </div>
        <button type="button" className="boton-cerrar" aria-label="Cerrar" onClick={onCancelar}>
          <IconoCerrar />
        </button>
      </header>
      <div className="panel-cuerpo">
        {errores.aviso === null ? null : <Aviso mensaje={errores.aviso} titulo={tituloDelAviso(errores.aviso)} />}
        <form onSubmit={guardar}>
          {usuario === null ? (
            <>
            <div className={errores.email === null ? 'campo' : 'campo campo-con-error'}>
              <div className="campo-etiqueta">
                <label htmlFor={idEmail} className="etiqueta-obligatoria">
                  Email
                </label>
              </div>
              <div className="entrada-con-icono">
                <input
                  id={idEmail}
                  type="email"
                  required
                  autoFocus
                  autoComplete="off"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  aria-invalid={errores.email === null ? undefined : true}
                  aria-describedby={errores.email === null ? undefined : idErrorEmail}
                />
                {errores.email === null ? null : <IconoAlerta clase="icono icono-en-campo" />}
              </div>
              {errores.email === null ? null : (
                <p id={idErrorEmail} className="error-de-campo">
                  {errores.email}
                </p>
              )}
            </div>
            <div className={errores.contrasena === null ? 'campo' : 'campo campo-con-error'}>
              <div className="campo-etiqueta">
                <label htmlFor={idContrasena} className="etiqueta-obligatoria">
                  Contraseña inicial
                </label>
                <p id={idAyuda} className="ayuda">
                  {AYUDA_DE_LARGO}
                </p>
              </div>
              <div className="entrada-con-icono">
                <input
                  id={idContrasena}
                  type="password"
                  required
                  autoComplete="new-password"
                  value={contrasena}
                  onChange={(e) => setContrasena(e.target.value)}
                  aria-invalid={errores.contrasena === null ? undefined : true}
                  aria-describedby={errores.contrasena === null ? idAyuda : `${idAyuda} ${idErrorContrasena}`}
                />
                {errores.contrasena === null ? null : <IconoAlerta clase="icono icono-en-campo" />}
              </div>
              {errores.contrasena === null ? null : (
                <p id={idErrorContrasena} className="error-de-campo">
                  {errores.contrasena}
                </p>
              )}
            </div>
            </>
          ) : (
            <div className="campo">
              <span className="etiqueta-de-dato">Email</span>
              <p className="dato-de-solo-lectura">{usuario.email}</p>
            </div>
          )}
          <fieldset
            className="campo campo-roles"
            aria-describedby={errores.roles === null ? undefined : idErrorRoles}
          >
            <legend>Roles</legend>
            {ROLES.map((rol) => (
              <label key={rol} className="casilla-de-rol">
                <input type="checkbox" checked={marcados.has(rol)} onChange={(e) => alternar(rol, e.target.checked)} />
                {nombreDelRol(rol)}
              </label>
            ))}
            {errores.roles === null ? null : (
              <p id={idErrorRoles} className="error-de-campo">
                {errores.roles}
              </p>
            )}
          </fieldset>
          {usuario === null ? null : (
            <p className="nota-informativa nota-de-roles">
              <IconoInfo />
              {NOTA_DE_ROLES}
            </p>
          )}
          <div className="panel-pie">
            <button type="button" className="boton-secundario" onClick={onCancelar}>
              Cancelar
            </button>
            <button type="submit" className="boton-primario" disabled={guardando}>
              {guardando ? 'Guardando…' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </aside>
  )
}

interface PropiedadesDeRestablecimiento {
  usuario: Usuario
  guardando: boolean
  errores: ErroresDelPanel
  onGuardar(contrasena: string): void
  onCancelar(): void
}

/**
 * Tercer modo del panel lateral (design K16): restablecer la contraseña de otro usuario. Un solo campo, sin
 * repetición (D296); la contraseña vive solo en el estado de este formulario y se descarta al desmontarse.
 */
export function PanelDeRestablecimiento({
  usuario,
  guardando,
  errores,
  onGuardar,
  onCancelar,
}: PropiedadesDeRestablecimiento) {
  const idTitulo = useId()
  const idContrasena = useId()
  const idAyuda = useId()
  const idError = useId()
  const [contrasena, setContrasena] = useState('')

  function guardar(evento: SyntheticEvent<HTMLFormElement>): void {
    evento.preventDefault()
    onGuardar(contrasena)
  }

  return (
    <aside aria-labelledby={idTitulo} className="panel-lateral panel-de-usuario">
      <header className="panel-encabezado">
        <div>
          <h2 id={idTitulo}>
            <IconoLlave />
            Restablecer contraseña
          </h2>
        </div>
        <button type="button" className="boton-cerrar" aria-label="Cerrar" onClick={onCancelar}>
          <IconoCerrar />
        </button>
      </header>
      <div className="panel-cuerpo">
        {errores.aviso === null ? null : <Aviso mensaje={errores.aviso} titulo={tituloDelAviso(errores.aviso)} />}
        <form onSubmit={guardar}>
          <div className="campo">
            <span className="etiqueta-de-dato">Email</span>
            <p className="dato-de-solo-lectura">{usuario.email}</p>
          </div>
          <div className={errores.contrasena === null ? 'campo' : 'campo campo-con-error'}>
            <div className="campo-etiqueta">
              <label htmlFor={idContrasena}>Contraseña nueva</label>
            </div>
            <div className="entrada-con-icono">
              <input
                id={idContrasena}
                type="password"
                required
                autoFocus
                autoComplete="new-password"
                value={contrasena}
                onChange={(e) => setContrasena(e.target.value)}
                aria-invalid={errores.contrasena === null ? undefined : true}
                aria-describedby={errores.contrasena === null ? idAyuda : `${idAyuda} ${idError}`}
              />
              {errores.contrasena === null ? null : <IconoAlerta clase="icono icono-en-campo" />}
            </div>
            <p id={idAyuda} className="ayuda">
              {AYUDA_DE_LARGO}
            </p>
            {errores.contrasena === null ? null : (
              <p id={idError} className="error-de-campo">
                {errores.contrasena}
              </p>
            )}
          </div>
          <p className="nota-informativa nota-de-roles">
            <IconoInfo />
            {NOTA_DE_RESTABLECER}
          </p>
          <div className="panel-pie">
            <button type="button" className="boton-secundario" onClick={onCancelar}>
              Cancelar
            </button>
            <button type="submit" className="boton-primario" disabled={guardando}>
              {guardando ? 'Guardando…' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </aside>
  )
}
