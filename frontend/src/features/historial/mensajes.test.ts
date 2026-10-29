import { describe, expect, it } from 'vitest'
import { EVENTO_CREADO_DEL_TURNO_11 } from '../../test/servidorFalso'
import {
  cuandoOcurrio,
  detalleDelCancelado,
  detalleDelCreado,
  detalleDelReprogramado,
  textoDelActor,
  tituloDelEvento,
} from './mensajes'

const ZONA = 'America/Argentina/Buenos_Aires'

describe('mensajes del historial', () => {
  it('HIS-2a: el creado se titula Turno creado', () => {
    expect(tituloDelEvento('creado')).toBe('Turno creado')
  })

  it('HIS-2a: cuándo ocurrió en hora del consultorio', () => {
    expect(cuandoOcurrio('2026-10-26T13:15:00Z', ZONA)).toBe('lunes 26 de octubre de 2026, 10:15')
  })

  it('HIS-2a: el actor con id', () => {
    expect(textoDelActor('usuario', '2')).toBe('Por: Usuario n.º 2')
  })

  it('HIS-2a: el detalle del creado', () => {
    expect(detalleDelCreado(EVENTO_CREADO_DEL_TURNO_11.despues, ZONA)).toBe('Estado inicial: Reservado · 09:00 – 09:30')
  })

  it('HIS-2b: un actor sin id es el usuario del panel sin identificar', () => {
    expect(textoDelActor('usuario', null)).toBe('Por: Usuario del panel (sin identificar)')
  })

  it('HIS-2b: un tipo desconocido es Cambio registrado', () => {
    expect(tituloDelEvento('confirmado')).toBe('Cambio registrado (confirmado)')
  })

  it('HIS-2b: el reprogramado se titula Turno reprogramado', () => {
    expect(tituloDelEvento('reprogramado')).toBe('Turno reprogramado')
  })

  it('HIS-2b: el cancelado se titula Turno cancelado', () => {
    expect(tituloDelEvento('cancelado')).toBe('Turno cancelado')
  })

  it('HIS-2b: el cambio de estado con las etiquetas de la agenda', () => {
    expect(detalleDelCancelado({ estado: 'reservado' }, { estado: 'cancelado_paciente' })).toBe(
      'Estado: Reservado → Cancelado por el paciente',
    )
  })

  it('HIS-2b: un cancelado por el consultorio', () => {
    expect(detalleDelCancelado({ estado: 'confirmado' }, { estado: 'cancelado_profesional' })).toBe(
      'Estado: Confirmado → Cancelado por el consultorio',
    )
  })

  it('HIS-2b: un cancelado sin estado en despues no tiene la línea Estado', () => {
    expect(detalleDelCancelado({ estado: 'confirmado' }, {})).toBeNull()
    expect(detalleDelCancelado({ estado: 'confirmado' }, null)).toBeNull()
    expect(detalleDelCancelado(null, { estado: 'cancelado_paciente' })).toBeNull()
    expect(detalleDelCancelado({}, { estado: 'cancelado_paciente' })).toBeNull()
  })

  it('HIS-2b: un cancelado con un estado desconocido no tiene la línea Estado', () => {
    expect(detalleDelCancelado({ estado: 'confirmado' }, { estado: 'raro' })).toBeNull()
    expect(detalleDelCancelado({ estado: 7 }, { estado: 'cancelado_paciente' })).toBeNull()
  })

  it('HIS-2b: el antes y el después en hora del consultorio', () => {
    const antes = { inicio: '2026-11-02T12:00:00Z', fin: '2026-11-02T12:45:00Z', duracion_minutos: 45 }
    const despues = { inicio: '2026-11-02T13:00:00Z', fin: '2026-11-02T13:45:00Z', duracion_minutos: 45 }
    expect(detalleDelReprogramado(antes, despues, ZONA)).toEqual([
      'Antes: lunes 2 de noviembre de 2026, 09:00 – 09:45 (45 min)',
      'Después: lunes 2 de noviembre de 2026, 10:00 – 10:45 (45 min)',
    ])
  })

  it('HIS-2b: la fecha es la del consultorio y no la de UTC', () => {
    expect(cuandoOcurrio('2026-11-01T02:30:00Z', ZONA)).toBe('sábado 31 de octubre de 2026, 23:30')
  })

  it('G4: un actor_tipo desconocido se muestra tal cual', () => {
    expect(textoDelActor('sistema', null)).toBe('Por: sistema')
  })

  it('G5: un despues incompleto no tiene detalle', () => {
    expect(detalleDelCreado({ estado: 'reservado', inicio: '2026-11-02T12:00:00Z' }, ZONA)).toBeNull()
    expect(detalleDelCreado({ estado: 'raro', inicio: '2026-11-02T12:00:00Z', fin: '2026-11-02T12:30:00Z' }, ZONA)).toBeNull()
    expect(detalleDelCreado(null, ZONA)).toBeNull()
  })

  it('HIS-2b: un reprogramado sin inicio en despues no tiene Antes ni Después', () => {
    const antes = { inicio: '2026-11-02T12:00:00Z', fin: '2026-11-02T12:45:00Z', duracion_minutos: 45 }
    expect(detalleDelReprogramado(antes, { fin: '2026-11-02T13:45:00Z', duracion_minutos: 45 }, ZONA)).toEqual([])
    expect(detalleDelReprogramado(antes, null, ZONA)).toEqual([])
  })

  it('HIS-2b: un reprogramado sin duracion_minutos no tiene Antes ni Después', () => {
    const antes = { inicio: '2026-11-02T12:00:00Z', fin: '2026-11-02T12:45:00Z', duracion_minutos: 45 }
    const despues = { inicio: '2026-11-02T13:00:00Z', fin: '2026-11-02T13:45:00Z' }
    expect(detalleDelReprogramado(antes, despues, ZONA)).toEqual([])
    expect(detalleDelReprogramado(antes, { ...despues, duracion_minutos: '45' }, ZONA)).toEqual([])
    expect(detalleDelReprogramado({ ...antes, duracion_minutos: 45.5 }, { ...despues, duracion_minutos: 45 }, ZONA)).toEqual([])
  })

  it('HIS-2b: el antes y el después en otro día del consultorio', () => {
    const antes = { inicio: '2026-11-02T12:00:00Z', fin: '2026-11-02T12:45:00Z', duracion_minutos: 45 }
    const despues = { inicio: '2026-11-04T01:00:00Z', fin: '2026-11-04T01:45:00Z', duracion_minutos: 45 }
    expect(detalleDelReprogramado(antes, despues, ZONA)).toEqual([
      'Antes: lunes 2 de noviembre de 2026, 09:00 – 09:45 (45 min)',
      'Después: martes 3 de noviembre de 2026, 22:00 – 22:45 (45 min)',
    ])
  })
})
