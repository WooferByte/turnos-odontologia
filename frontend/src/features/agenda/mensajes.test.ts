import { describe, expect, it } from 'vitest'
import { ESTADOS_DEL_TURNO } from './apiAgenda'
import { ETIQUETAS_DE_ESTADO, TONOS_DE_ESTADO, diaCompacto, nombreDelDia, sumarDias, textoDelContador } from './mensajes'

describe('mensajes de la agenda', () => {
  it.each([
    ['2026-11-02', 'lunes 2 de noviembre de 2026'],
    ['2026-11-03', 'martes 3 de noviembre de 2026'],
    ['2027-01-01', 'viernes 1 de enero de 2027'],
    ['2026-02-28', 'sábado 28 de febrero de 2026'],
    ['2026-11-01', 'domingo 1 de noviembre de 2026'],
  ])('AGE-4a: el nombre del día de %s es «%s» (sin coma, listas fijas)', (fecha, esperado) => {
    expect(nombreDelDia(fecha)).toBe(esperado)
  })

  it.each([
    ['2026-11-02', 'lun 02/11/2026'],
    ['2026-12-31', 'jue 31/12/2026'],
  ])('AGE-4b: el día compacto de %s es «%s»', (fecha, esperado) => {
    expect(diaCompacto(fecha)).toBe(esperado)
  })

  it.each([
    ['2026-11-02', 1, '2026-11-03'],
    ['2026-11-30', 1, '2026-12-01'],
    ['2026-12-31', 1, '2027-01-01'],
    ['2026-03-01', -1, '2026-02-28'],
    ['2028-03-01', -1, '2028-02-29'],
    ['2027-01-01', -1, '2026-12-31'],
  ])('AGE-4b: sumarDias(%s, %i) es %s (días de calendario, sin hora ni zona)', (fecha, dias, esperado) => {
    expect(sumarDias(fecha, dias)).toBe(esperado)
  })

  it('AGE-4c: los nueve estados tienen etiqueta y tono', () => {
    expect(ESTADOS_DEL_TURNO.map((estado) => ETIQUETAS_DE_ESTADO[estado])).toEqual([
      'Pendiente de aprobación',
      'Pendiente de seña',
      'Reservado',
      'Confirmado',
      'Cancelado por el paciente',
      'Cancelado por el consultorio',
      'Vencido',
      'Atendido',
      'Ausente',
    ])
    expect(ESTADOS_DEL_TURNO.map((estado) => TONOS_DE_ESTADO[estado])).toEqual([
      'ambar',
      'ambar',
      'celeste',
      'verde',
      'rojo',
      'rojo',
      'rojo',
      'verde',
      'rojo',
    ])
  })

  it('AGE-4a: el contador usa el singular con un solo turno', () => {
    expect([0, 1, 3].map(textoDelContador)).toEqual(['0 turnos', '1 turno', '3 turnos'])
  })
})
