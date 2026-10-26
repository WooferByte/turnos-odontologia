// Alta de un bloqueo (design B14, B16): alcance, recurso, desde, hasta y motivo. Los valores viven en la pantalla;
// acá solo se dibujan. Sin validación local del orden de las fechas ni del largo del motivo (D286).
import type { FormEvent } from 'react'
import { IconoAlerta } from '../../shared/iconos/IconoAlerta'
import { IconoCalendario } from '../../shared/iconos/IconoCalendario'
import { IconoCandado } from '../../shared/iconos/IconoCandado'
import type { Profesional } from '../horario/apiHorario'
import type { Sillon } from './apiBloqueos'

export type AlcanceElegido = 'consultorio' | 'profesional' | 'sillon'

/** Lo que escribió la persona; `desde` y `hasta` son valores de `datetime-local` (hora del consultorio). */
export interface ValoresDelFormulario {
  alcance: AlcanceElegido
  /** Id del profesional o del sillón elegido, como texto; vacío si no eligió. */
  recurso: string
  desde: string
  hasta: string
  motivo: string
}

export const FORMULARIO_VACIO: ValoresDelFormulario = {
  alcance: 'profesional',
  recurso: '',
  desde: '',
  hasta: '',
  motivo: '',
}

interface Propiedades {
  valores: ValoresDelFormulario
  /** Solo los activos: uno inactivo daría `RN-GL-04` (hallazgo H9). */
  profesionales: readonly Profesional[]
  sillones: readonly Sillon[]
  enviando: boolean
  /** El rechazo `RN-AG-17` marca «Hasta» con borde rojo. */
  hastaInvalido: boolean
  onCambiar(cambio: Partial<ValoresDelFormulario>): void
  onEnviar(): void
}

export function FormularioDeBloqueo({
  valores,
  profesionales,
  sillones,
  enviando,
  hastaInvalido,
  onCambiar,
  onEnviar,
}: Propiedades) {
  function enviar(evento: FormEvent): void {
    evento.preventDefault()
    onEnviar()
  }

  const recursos =
    valores.alcance === 'profesional'
      ? profesionales.map((p) => ({ id: p.id, nombre: p.nombre }))
      : sillones.map((s) => ({ id: s.id, nombre: s.nombre }))

  return (
    <section className="tarjeta tarjeta-de-alta" aria-labelledby="titulo-nuevo-bloqueo">
      <div className="tarjeta-encabezado">
        <h2 id="titulo-nuevo-bloqueo">
          <IconoCalendario />
          Nuevo bloqueo
        </h2>
      </div>
      <form className="formulario-de-bloqueo" onSubmit={enviar} noValidate>
        <div className="campo">
          <label htmlFor="bloqueo-alcance">Alcance</label>
          <select
            id="bloqueo-alcance"
            value={valores.alcance}
            onChange={(evento) => onCambiar({ alcance: evento.target.value as AlcanceElegido, recurso: '' })}
          >
            <option value="consultorio">Todo el consultorio</option>
            <option value="profesional">Un profesional</option>
            <option value="sillon">Un sillón</option>
          </select>
        </div>
        {valores.alcance === 'consultorio' ? null : (
          <div className="campo">
            <label htmlFor="bloqueo-recurso">{valores.alcance === 'profesional' ? 'Profesional' : 'Sillón'}</label>
            <select
              id="bloqueo-recurso"
              value={valores.recurso}
              onChange={(evento) => onCambiar({ recurso: evento.target.value })}
            >
              <option value="">Elegí una opción</option>
              {recursos.map((recurso) => (
                <option key={recurso.id} value={recurso.id}>
                  {recurso.nombre}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="fechas-del-bloqueo">
          <div className="campo">
            <label htmlFor="bloqueo-desde">Desde</label>
            <input
              id="bloqueo-desde"
              type="datetime-local"
              value={valores.desde}
              onChange={(evento) => onCambiar({ desde: evento.target.value })}
            />
          </div>
          <div className={hastaInvalido ? 'campo campo-con-error' : 'campo'}>
            <label htmlFor="bloqueo-hasta">Hasta</label>
            <input
              id="bloqueo-hasta"
              type="datetime-local"
              value={valores.hasta}
              aria-invalid={hastaInvalido ? 'true' : undefined}
              onChange={(evento) => onCambiar({ hasta: evento.target.value })}
            />
            {hastaInvalido ? <IconoAlerta clase="icono icono-en-fecha" /> : null}
          </div>
        </div>
        <div className="campo">
          <label htmlFor="bloqueo-motivo">Motivo</label>
          <input
            id="bloqueo-motivo"
            type="text"
            value={valores.motivo}
            placeholder="Ej.: Ausencia, Vacaciones, Feriado"
            onChange={(evento) => onCambiar({ motivo: evento.target.value })}
          />
        </div>
        <button type="submit" className="boton-primario boton-de-ancho-completo" disabled={enviando}>
          <IconoCandado />
          Bloquear
        </button>
      </form>
    </section>
  )
}
