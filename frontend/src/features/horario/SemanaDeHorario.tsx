// Las siete filas de la semana (design H14, H15): una región por día con sus franjas editables o «Sin atención».
import { IconoAlerta } from '../../shared/iconos/IconoAlerta'
import { IconoMas } from '../../shared/iconos/IconoMas'
import { IconoPapelera } from '../../shared/iconos/IconoPapelera'
import type { FranjaEditable, Marca } from './edicion'
import { MENSAJE_FRANJA_INCOMPLETA, MENSAJE_RN_AG_16, MENSAJE_SIN_ATENCION } from './mensajes'

export const DIAS_DE_LA_SEMANA = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'] as const

interface Propiedades {
  editables: readonly FranjaEditable[]
  marcas: ReadonlyMap<number, Marca>
  onAgregar: (dia: number) => void
  onQuitar: (clave: number) => void
  onCambiar: (clave: number, campo: 'inicio' | 'fin', valor: string) => void
}

export function SemanaDeHorario({ editables, marcas, onAgregar, onQuitar, onCambiar }: Propiedades) {
  return (
    <div className="semana-de-horario">
      {DIAS_DE_LA_SEMANA.map((nombre, dia) => {
        const delDia = editables.filter((f) => f.dia_semana === dia)
        const marcasDelDia = delDia.map((f) => marcas.get(f.clave))
        const hayInvalida = marcasDelDia.includes('invalida')
        const hayIncompleta = marcasDelDia.includes('incompleta')
        const clase = ['dia-de-horario', hayInvalida ? 'dia-con-error' : '', delDia.length === 0 ? 'dia-vacio' : '']
        return (
          <section key={nombre} className={clase.join(' ').trim()} aria-labelledby={`dia-${dia}`}>
            <h3 id={`dia-${dia}`} className="nombre-del-dia">
              {nombre}
            </h3>
            <div className="contenido-del-dia">
              <div className="franjas-del-dia">
                {delDia.length === 0 ? <span className="sin-atencion">{MENSAJE_SIN_ATENCION}</span> : null}
                {delDia.map((franja, i) => {
                  const marca = marcas.get(franja.clave)
                  return (
                    <div
                      key={franja.clave}
                      role="group"
                      aria-label={`Franja ${i + 1}`}
                      className={marca === undefined ? 'franja-de-horario' : 'franja-de-horario franja-con-error'}
                    >
                      <label>
                        Desde
                        <input
                          type="time"
                          step={60}
                          value={franja.inicio}
                          aria-invalid={marca === 'invalida' || (marca === 'incompleta' && franja.inicio === '') ? 'true' : undefined}
                          onChange={(evento) => onCambiar(franja.clave, 'inicio', evento.target.value)}
                        />
                      </label>
                      <label>
                        Hasta
                        <input
                          type="time"
                          step={60}
                          value={franja.fin}
                          aria-invalid={marca === 'invalida' || (marca === 'incompleta' && franja.fin === '') ? 'true' : undefined}
                          onChange={(evento) => onCambiar(franja.clave, 'fin', evento.target.value)}
                        />
                      </label>
                      <button
                        type="button"
                        className="boton-quitar-franja"
                        aria-label="Quitar franja"
                        onClick={() => onQuitar(franja.clave)}
                      >
                        <IconoPapelera />
                      </button>
                    </div>
                  )
                })}
                <button type="button" className="boton-agregar-franja" onClick={() => onAgregar(dia)}>
                  <IconoMas />
                  Agregar franja
                </button>
              </div>
              {hayInvalida ? (
                <p className="error-de-dia">
                  <IconoAlerta />
                  {MENSAJE_RN_AG_16}
                </p>
              ) : null}
              {hayIncompleta ? (
                <p className="error-de-dia">
                  <IconoAlerta />
                  {MENSAJE_FRANJA_INCOMPLETA}
                </p>
              ) : null}
            </div>
          </section>
        )
      })}
    </div>
  )
}
