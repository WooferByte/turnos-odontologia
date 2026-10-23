// Estado editable de la semana (design H15): funciones puras sobre las franjas que se están editando. La pantalla no
// evalúa reglas: solo ordena el cuerpo, compara con lo recibido y exige las dos horas de cada franja.
import type { Franja } from './apiHorario'

/** Una franja en edición: `clave` la identifica aunque cambien sus horas; las horas vacías son `''`. */
export interface FranjaEditable {
  clave: number
  dia_semana: number
  inicio: string
  fin: string
}

/** Por qué se marca una franja: le falta una hora (local) o la API la informó con `RN-AG-16`. */
export type Marca = 'incompleta' | 'invalida'

export function aEditables(franjas: readonly Franja[], nuevaClave: () => number): FranjaEditable[] {
  return franjas.map((f) => ({
    clave: nuevaClave(),
    dia_semana: f.dia_semana,
    inicio: f.hora_inicio,
    fin: f.hora_fin,
  }))
}

export function estaIncompleta(franja: FranjaEditable): boolean {
  return franja.inicio === '' || franja.fin === ''
}

/** Las franjas en el orden del cuerpo del `PUT`: por día y por hora de inicio (estable). */
export function enOrdenDelCuerpo(editables: readonly FranjaEditable[]): FranjaEditable[] {
  return [...editables].sort((a, b) => a.dia_semana - b.dia_semana || a.inicio.localeCompare(b.inicio))
}

export function aFranjas(ordenadas: readonly FranjaEditable[]): Franja[] {
  return ordenadas.map((f) => ({ dia_semana: f.dia_semana, hora_inicio: f.inicio, hora_fin: f.fin }))
}

export function mismasFranjas(a: readonly Franja[], b: readonly Franja[]): boolean {
  return (
    a.length === b.length &&
    a.every((f, i) => {
      const otra = b[i]
      return (
        otra !== undefined &&
        f.dia_semana === otra.dia_semana &&
        f.hora_inicio === otra.hora_inicio &&
        f.hora_fin === otra.hora_fin
      )
    })
  )
}

const CAMPO_DE_FRANJA = /^franjas\.(\d+)$/

/** Las claves de las franjas que la API informó (`franjas.<i>` es la posición en el cuerpo enviado). */
export function clavesInformadas(
  errores: readonly { campo: string | null }[],
  enviadas: readonly FranjaEditable[],
): number[] {
  return errores.flatMap((error) => {
    const posicion = CAMPO_DE_FRANJA.exec(error.campo ?? '')?.[1]
    const franja = posicion === undefined ? undefined : enviadas[Number(posicion)]
    return franja === undefined ? [] : [franja.clave]
  })
}
