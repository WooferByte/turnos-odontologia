// «Mi contraseña» (design K15): cada usuario cambia la suya. La repetición se compara en el navegador antes de
// mandar (D296); el largo y la contraseña actual los decide la API (D232). Las contraseñas viven solo en el estado
// de este formulario y se descartan al salir de la pantalla. Con el `200`, los tokens nuevos reemplazan a los de
// la sesión (D291) para que esta sesión siga sin renovar.
import { useId, useMemo, useState, type SyntheticEvent } from 'react'
import { SesionTerminada } from '../../shared/api/errores'
import { useSesionDelPanel } from '../../shared/api/ProveedorDeSesion'
import { Aviso } from '../../shared/componentes/Aviso'
import { AvisoDeExito } from '../../shared/componentes/AvisoDeExito'
import { IconoAlerta } from '../../shared/iconos/IconoAlerta'
import { IconoCandado } from '../../shared/iconos/IconoCandado'
import { tituloDelAviso } from '../usuarios/mensajes'
import { crearApiContrasenas } from './apiContrasenas'
import {
  AVISO_DE_CAMBIADA,
  AYUDA_DE_LARGO,
  erroresDeCambioPropio,
  MENSAJE_REPETICION_DISTINTA,
  SIN_ERRORES_DE_MI_CONTRASENA,
  type ErroresDeMiContrasena,
} from './mensajes'

interface PropiedadesDeCampo {
  id: string
  etiqueta: string
  valor: string
  autoComplete: 'current-password' | 'new-password'
  error: string | null
  ayuda?: string
  autoFocus?: boolean
  onCambio(valor: string): void
}

function CampoDeContrasena({
  id,
  etiqueta,
  valor,
  autoComplete,
  error,
  ayuda,
  autoFocus,
  onCambio,
}: PropiedadesDeCampo) {
  const idError = `${id}-error`
  const idAyuda = `${id}-ayuda`
  const descripcion = [ayuda === undefined ? null : idAyuda, error === null ? null : idError].filter(
    (x) => x !== null,
  )
  return (
    <div className={error === null ? 'campo' : 'campo campo-con-error'}>
      <div className="campo-etiqueta">
        <label htmlFor={id}>{etiqueta}</label>
      </div>
      <div className="entrada-con-icono">
        <input
          id={id}
          type="password"
          required
          autoFocus={autoFocus === true}
          autoComplete={autoComplete}
          value={valor}
          onChange={(e) => onCambio(e.target.value)}
          aria-invalid={error === null ? undefined : true}
          aria-describedby={descripcion.length === 0 ? undefined : descripcion.join(' ')}
        />
      </div>
      {ayuda === undefined ? null : (
        <p id={idAyuda} className="ayuda">
          {ayuda}
        </p>
      )}
      {error === null ? null : (
        <p id={idError} className="error-de-campo error-de-campo-con-icono">
          <IconoAlerta clase="icono icono-de-error" />
          {error}
        </p>
      )}
    </div>
  )
}

export function PaginaMiContrasena() {
  const { pedidoDelPanel, reemplazarTokens } = useSesionDelPanel()
  const api = useMemo(() => crearApiContrasenas(pedidoDelPanel), [pedidoDelPanel])
  const idBase = useId()
  const [actual, setActual] = useState('')
  const [nueva, setNueva] = useState('')
  const [repeticion, setRepeticion] = useState('')
  const [errores, setErrores] = useState<ErroresDeMiContrasena>(SIN_ERRORES_DE_MI_CONTRASENA)
  const [exito, setExito] = useState(false)
  const [guardando, setGuardando] = useState(false)

  async function cambiar(evento: SyntheticEvent<HTMLFormElement>): Promise<void> {
    evento.preventDefault()
    setExito(false)
    if (nueva !== repeticion) {
      setErrores({ ...SIN_ERRORES_DE_MI_CONTRASENA, repeticion: MENSAJE_REPETICION_DISTINTA })
      return
    }
    setGuardando(true)
    setErrores(SIN_ERRORES_DE_MI_CONTRASENA)
    try {
      const tokens = await api.cambiarContrasena(actual, nueva)
      reemplazarTokens(tokens.access, tokens.refresh)
      setActual('')
      setNueva('')
      setRepeticion('')
      setExito(true)
    } catch (error: unknown) {
      if (!(error instanceof SesionTerminada)) setErrores(erroresDeCambioPropio(error))
    } finally {
      setGuardando(false)
    }
  }

  return (
    <section aria-labelledby="titulo-mi-contrasena" className="pantalla-de-contrasena">
      <h1 id="titulo-mi-contrasena">Mi contraseña</h1>
      <section className="tarjeta tarjeta-de-contrasena">
        {errores.aviso === null ? null : <Aviso mensaje={errores.aviso} titulo={tituloDelAviso(errores.aviso)} />}
        <form onSubmit={(evento) => void cambiar(evento)}>
          <CampoDeContrasena
            id={`${idBase}-actual`}
            etiqueta="Contraseña actual"
            valor={actual}
            autoComplete="current-password"
            error={errores.actual}
            autoFocus
            onCambio={setActual}
          />
          <CampoDeContrasena
            id={`${idBase}-nueva`}
            etiqueta="Contraseña nueva"
            valor={nueva}
            autoComplete="new-password"
            error={errores.nueva}
            ayuda={AYUDA_DE_LARGO}
            onCambio={setNueva}
          />
          <CampoDeContrasena
            id={`${idBase}-repeticion`}
            etiqueta="Repetir contraseña nueva"
            valor={repeticion}
            autoComplete="new-password"
            error={errores.repeticion}
            onCambio={setRepeticion}
          />
          <button type="submit" className="boton-primario boton-de-ancho-completo" disabled={guardando}>
            <IconoCandado />
            {guardando ? 'Cambiando…' : 'Cambiar contraseña'}
          </button>
        </form>
      </section>
      {exito ? <AvisoDeExito mensaje={AVISO_DE_CAMBIADA} /> : null}
    </section>
  )
}
