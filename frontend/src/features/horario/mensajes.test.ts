import { describe, expect, it } from 'vitest'
import { EntradaRechazada, PermisoInsuficiente, RecursoInexistente, SinConexion } from '../../shared/api/errores'
import { etiquetaDelProfesional, mensajeDeRechazo, tituloDelAviso } from './mensajes'

const CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'

describe('mensajes del horario', () => {
  it('H17: un 422 sin código da «Revisá las franjas del horario.»', () => {
    const sinCodigo = new EntradaRechazada('Entrada rechazada.', null, [], [
      { campo: 'franjas', codigo: null, mensaje: 'x' },
    ])

    expect(mensajeDeRechazo(sinCodigo)).toBe('Revisá las franjas del horario.')
  })

  it('H17: RN-AG-16, el permiso, el profesional y la conexión tienen cada uno su mensaje', () => {
    const superpuestas = new EntradaRechazada('Entrada rechazada.', 'RN-AG-16', ['RN-AG-16'], [])

    expect(mensajeDeRechazo(superpuestas)).toBe(
      'Hay franjas que se superponen o no terminan después de empezar (RN-AG-16).',
    )
    expect(mensajeDeRechazo(new PermisoInsuficiente('p', 'RN-AU-05'))).toBe(
      'Tu usuario no tiene permiso para modificar el horario (RN-AU-05).',
    )
    expect(mensajeDeRechazo(new RecursoInexistente('r', 'RN-GL-04'))).toBe('El profesional ya no existe (RN-GL-04).')
    expect(mensajeDeRechazo(new SinConexion('s', null))).toBe(CONEXION)
    expect(mensajeDeRechazo(new TypeError('Failed to fetch'))).toBe(CONEXION)
  })

  it('H15: el inactivo lleva «(inactivo)» y solo el permiso y la conexión llevan título', () => {
    expect(etiquetaDelProfesional({ id: 1, nombre: 'Dra. Demo Ficticia', activo: true })).toBe('Dra. Demo Ficticia')
    expect(etiquetaDelProfesional({ id: 2, nombre: 'Dr. Ejemplo Ficticio', activo: false })).toBe(
      'Dr. Ejemplo Ficticio (inactivo)',
    )
    expect(tituloDelAviso('Tu usuario no tiene permiso para modificar el horario (RN-AU-05).')).toBe(
      'Acceso restringido',
    )
    expect(tituloDelAviso(CONEXION)).toBe('Sin conexión')
    expect(tituloDelAviso('El profesional ya no existe (RN-GL-04).')).toBeNull()
  })
})
