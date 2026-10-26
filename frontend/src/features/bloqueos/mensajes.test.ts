import { describe, expect, it } from 'vitest'
import { EntradaRechazada, PermisoInsuficiente, RecursoInexistente, SinConexion } from '../../shared/api/errores'
import type { Bloqueo, Sillon, TurnoAfectado } from './apiBloqueos'
import { avisoDeCreado, etiquetaDelAlcance, filaDeTurnoAfectado, mensajeDeRechazo, tituloDelAviso } from './mensajes'

const ZONA = 'America/Argentina/Buenos_Aires'
const CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'

function bloqueo(parte: Partial<Bloqueo>): Bloqueo {
  return {
    id: 1,
    alcance: 'consultorio',
    profesional_id: null,
    sillon_id: null,
    inicio: '2026-11-23T03:00:00Z',
    fin: '2026-11-24T03:00:00Z',
    motivo: 'Feriado',
    creado_por: 1,
    ...parte,
  }
}

describe('mensajes de los bloqueos', () => {
  it('B17: con un turno afectado el aviso dice «Hay 1 turno activo»', () => {
    expect(avisoDeCreado(1)).toContain('Hay 1 turno activo en ese horario')
    expect(avisoDeCreado(1)).not.toContain('turnos')
  })

  it('B17: sin turnos y con varios el aviso cambia', () => {
    expect(avisoDeCreado(0)).toBe('Bloqueo creado. No hay turnos activos en ese horario.')
    expect(avisoDeCreado(3)).toBe(
      'Bloqueo creado. Hay 3 turnos activos en ese horario: no se cancelaron, hay que reprogramarlos o cancelarlos.',
    )
  })

  it('B17: la fila de un turno afectado va en hora del consultorio', () => {
    const turno: TurnoAfectado = {
      id: 7,
      inicio: '2026-11-02T13:00:00Z',
      fin: '2026-11-02T13:30:00Z',
      estado: 'reservado',
      profesional_id: 1,
      sillon_id: 1,
      paciente_id: 1,
    }

    expect(filaDeTurnoAfectado(turno, ZONA)).toBe('Turno 7 · 02/11/2026 10:00 a 10:30')
  })

  it('B17: el alcance se nombra con el recurso, o solo por su número si ya no está en la lista', () => {
    const sillones: Sillon[] = [{ id: 3, nombre: 'Sillón 3', activo: true }]
    const profesionales = [{ id: 1, nombre: 'Dra. Demo Ficticia', activo: false }]

    expect(etiquetaDelAlcance(bloqueo({}), profesionales, sillones)).toBe('Todo el consultorio')
    expect(etiquetaDelAlcance(bloqueo({ alcance: 'profesional', profesional_id: 1 }), profesionales, sillones)).toBe(
      'Profesional: Dra. Demo Ficticia',
    )
    expect(etiquetaDelAlcance(bloqueo({ alcance: 'sillon', sillon_id: 3 }), profesionales, sillones)).toBe(
      'Sillón: Sillón 3',
    )
    expect(etiquetaDelAlcance(bloqueo({ alcance: 'sillon', sillon_id: 9 }), profesionales, sillones)).toBe(
      'Sillón: Nº 9',
    )
  })

  it('B17: cada rechazo tiene su mensaje y el 404 depende de la acción', () => {
    const invertido = new EntradaRechazada('Entrada rechazada.', 'RN-AG-17', ['RN-AG-17'], [])
    const recurso = new EntradaRechazada('Entrada rechazada.', 'RN-GL-04', ['RN-GL-04'], [])
    const sinCodigo = new EntradaRechazada('Entrada rechazada.', null, [], [])

    expect(mensajeDeRechazo(invertido, 'crear')).toBe('El bloqueo tiene que terminar después de empezar (RN-AG-17).')
    expect(mensajeDeRechazo(recurso, 'crear')).toBe(
      'El profesional o el sillón elegido ya no está disponible (RN-GL-04).',
    )
    expect(mensajeDeRechazo(sinCodigo, 'crear')).toBe('Revisá los datos del bloqueo.')
    expect(mensajeDeRechazo(new PermisoInsuficiente('x', 'RN-AU-05'), 'eliminar')).toBe(
      'Tu usuario no tiene permiso para modificar los bloqueos (RN-AU-05).',
    )
    expect(mensajeDeRechazo(new RecursoInexistente('x', 'RN-GL-04'), 'eliminar')).toBe(
      'El bloqueo ya no existe (RN-GL-04).',
    )
    expect(mensajeDeRechazo(new SinConexion('x', null), 'crear')).toBe(CONEXION)
  })

  it('B17: solo el permiso y la conexión llevan título', () => {
    expect(tituloDelAviso(CONEXION)).toBe('Sin conexión')
    expect(tituloDelAviso('Tu usuario no tiene permiso para modificar los bloqueos (RN-AU-05).')).toBe(
      'Acceso restringido',
    )
    expect(tituloDelAviso('Revisá los datos del bloqueo.')).toBeNull()
  })
})
