import { describe, expect, it } from 'vitest'
import { EntradaRechazada, PermisoInsuficiente, RecursoInexistente, ReglaRechazada, SinConexion } from '../../shared/api/errores'
import { ESTADOS_DEL_TURNO } from './apiAgenda'
import {
  ETIQUETAS_DE_ESTADO,
  TONOS_DE_ESTADO,
  diaCompacto,
  mensajeDeCancelacion,
  mensajeDeReprogramacion,
  nombreDelDia,
  sumarDias,
  textoDelContador,
} from './mensajes'

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

  it('REP-7a: el texto de REP-1', () => {
    expect(mensajeDeReprogramacion(new ReglaRechazada('x', 'RN-AG-05', ['RN-AG-05', 'RN-AG-08']))).toBe(
      'El profesional y el sillón ya tienen un turno activo en ese horario (RN-AG-05, RN-AG-08).',
    )
    expect(mensajeDeReprogramacion(new ReglaRechazada('x', 'RN-AG-08'))).toBe(
      'El sillón ya tiene un turno activo en ese horario (RN-AG-08).',
    )
  })

  it.each([
    [new EntradaRechazada('x', 'RN-AG-01', ['RN-AG-01']), 'La duración debe ser mayor que 0 y múltiplo de 5 minutos (RN-AG-01).'],
    [new ReglaRechazada('x', 'RN-AG-18'), 'Este turno ya no se puede reprogramar por su estado (RN-AG-18).'],
    [new RecursoInexistente('x', 'RN-GL-04'), 'El turno ya no existe (RN-GL-04).'],
    [new PermisoInsuficiente('x', 'RN-AU-05'), 'Tu usuario no tiene permiso para reprogramar turnos (RN-AU-05).'],
    [new EntradaRechazada('x', 'RN-AG-04', ['RN-AG-04']), 'El turno no cae dentro del horario de atención del profesional (RN-AG-04).'],
    [new SinConexion('x', null), 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'],
  ])('REP-7b: RN-AG-01, RN-AG-18, el 404 y el 403 con su texto (%#)', (error, texto) => {
    expect(mensajeDeReprogramacion(error)).toBe(texto)
  })

  it('CAN-5a: el texto de RN-AG-12', () => {
    expect(mensajeDeCancelacion(new ReglaRechazada('x', 'RN-AG-12'))).toBe(
      'Este turno ya no se puede cancelar por su estado (RN-AG-12).',
    )
  })

  it.each([
    [new RecursoInexistente('x', 'RN-GL-04'), 'El turno ya no existe (RN-GL-04).'],
    [new PermisoInsuficiente('x', 'RN-AU-05'), 'Tu usuario no tiene permiso para cancelar turnos (RN-AU-05).'],
    [new SinConexion('x', null), 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'],
  ])('CAN-5b: el 404, el 403 y la conexión con su texto (%#)', (error, texto) => {
    expect(mensajeDeCancelacion(error)).toBe(texto)
  })

  it('CAN-4b: cancelado_profesional se ve como Cancelado por el consultorio', () => {
    expect(ETIQUETAS_DE_ESTADO.cancelado_profesional).toBe('Cancelado por el consultorio')
    expect(TONOS_DE_ESTADO.cancelado_profesional).toBe('rojo')
  })
})
