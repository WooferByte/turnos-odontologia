// Fecha y hora del consultorio que usan los paneles «Nuevo turno» y «Reprogramar» (design M11): el formato de los
// campos y la hora en que termina un turno.
import { aUtc, horaLocal } from '../../shared/horaDelConsultorio'

export const FECHA = /^\d{4}-\d{2}-\d{2}$/
export const HORA = /^\d{2}:\d{2}$/

/** `hh:mm` en que termina un turno que empieza en `fecha` y `hora` del consultorio, o `null` si falta algo. */
export function horaDeFin(fecha: string, hora: string, duracionMinutos: number, zona: string): string | null {
  if (!FECHA.test(fecha) || !HORA.test(hora)) return null
  const fin = new Date(Date.parse(aUtc(`${fecha}T${hora}`, zona)) + duracionMinutos * 60000)
  return horaLocal(fin.toISOString(), zona)
}
