// Las siete filas de la semana (design H14, H15): una región por día con sus franjas en orden o «Sin atención».
import type { Franja } from './apiHorario'
import { MENSAJE_SIN_ATENCION } from './mensajes'

export const DIAS_DE_LA_SEMANA = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'] as const

interface Propiedades {
  franjas: readonly Franja[]
}

export function SemanaDeHorario({ franjas }: Propiedades) {
  return (
    <div className="semana-de-horario">
      {DIAS_DE_LA_SEMANA.map((nombre, dia) => {
        const delDia = franjas.filter((f) => f.dia_semana === dia)
        return (
          <section key={nombre} className="dia-de-horario" aria-labelledby={`dia-${dia}`}>
            <h3 id={`dia-${dia}`} className="nombre-del-dia">
              {nombre}
            </h3>
            <div className="franjas-del-dia">
              {delDia.length === 0 ? <span className="sin-atencion">{MENSAJE_SIN_ATENCION}</span> : null}
              {delDia.map((franja, i) => (
                <div key={i} role="group" aria-label={`Franja ${i + 1}`} className="franja-de-horario">
                  <label>
                    Desde
                    <input type="time" step={60} value={franja.hora_inicio} readOnly />
                  </label>
                  <label>
                    Hasta
                    <input type="time" step={60} value={franja.hora_fin} readOnly />
                  </label>
                </div>
              ))}
            </div>
          </section>
        )
      })}
    </div>
  )
}
