import { describe, expect, it } from 'vitest'
import { aLocal, aUtc, fechaLocal, horaLocal } from './horaDelConsultorio'

const ZONA = 'America/Argentina/Buenos_Aires'

describe('horaDelConsultorio', () => {
  it('AGE-4a: horaLocal da la hora del consultorio', () => {
    expect(horaLocal('2026-11-02T12:00:00Z', ZONA)).toBe('09:00')
    expect(horaLocal('2026-11-02T15:00:00Z', ZONA)).toBe('12:00')
  })

  it('AGE-4a: horaLocal cruza la medianoche de UTC hacia el día anterior del consultorio', () => {
    expect(horaLocal('2026-11-03T02:59:00Z', ZONA)).toBe('23:59')
    expect(horaLocal('2026-11-03T03:00:00Z', ZONA)).toBe('00:00')
  })

  it('AGE-5h: fechaLocal da la fecha del consultorio, no la de UTC', () => {
    expect(fechaLocal('2026-11-04T01:00:00Z', ZONA)).toBe('2026-11-03')
    expect(fechaLocal('2026-11-02T03:00:00Z', ZONA)).toBe('2026-11-02')
  })

  it('AGE-5h: fechaLocal justo antes de la medianoche local sigue en el día anterior', () => {
    expect(fechaLocal('2026-11-02T02:59:00Z', ZONA)).toBe('2026-11-01')
  })

  it('US-003 CA-1: 23/11/2026 00:00 del consultorio es 2026-11-23T03:00:00Z y vuelve igual', () => {
    const utc = aUtc('2026-11-23T00:00', ZONA)

    expect(utc).toBe('2026-11-23T03:00:00Z')
    expect(aLocal(utc, ZONA)).toBe('23/11/2026 00:00')
  })

  it('US-003 CA-1: 21:30 del consultorio cae al día siguiente en UTC', () => {
    const utc = aUtc('2026-11-23T21:30', ZONA)

    expect(utc).toBe('2026-11-24T00:30:00Z')
    expect(aLocal(utc, ZONA)).toBe('23/11/2026 21:30')
  })

  it('US-003 CA-1: una fecha local en el borde de la medianoche se convierte bien', () => {
    expect(aUtc('2026-11-24T00:00', ZONA)).toBe('2026-11-24T03:00:00Z')
    expect(aUtc('2026-11-23T23:59', ZONA)).toBe('2026-11-24T02:59:00Z')
    expect(aLocal('2026-11-24T02:59:00Z', ZONA)).toBe('23/11/2026 23:59')
    expect(aLocal('2026-11-24T03:00:00Z', ZONA)).toBe('24/11/2026 00:00')
  })

  it('US-003 CA-1: una zona con cambio de hora usa el desfase de cada instante', () => {
    // Nueva York: UTC-4 en verano y UTC-5 después del 1/11/2026.
    expect(aUtc('2026-07-01T12:00', 'America/New_York')).toBe('2026-07-01T16:00:00Z')
    expect(aUtc('2026-11-02T12:00', 'America/New_York')).toBe('2026-11-02T17:00:00Z')
    expect(aLocal('2026-11-02T17:00:00Z', 'America/New_York')).toBe('02/11/2026 12:00')
  })
})
