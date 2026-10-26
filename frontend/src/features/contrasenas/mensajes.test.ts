import { describe, expect, it } from 'vitest'
import { EntradaRechazada, PermisoInsuficiente } from '../../shared/api/errores'
import { erroresDeCambioPropio, erroresDeRestablecimiento } from './mensajes'

// Funciones puras: el rechazo se arma en el test, sin servidor ni mocks (design K14).
describe('mensajes de contraseñas', () => {
  it('K14: un 403 al cambiar la propia da su mensaje', () => {
    const errores = erroresDeCambioPropio(new PermisoInsuficiente('Permiso insuficiente.', 'RN-AU-05'))

    expect(errores).toEqual({
      actual: null,
      nueva: null,
      repeticion: null,
      aviso: 'Tu usuario no tiene permiso para cambiar la contraseña (RN-AU-05).',
    })
  })

  it('K14: un 422 de un campo sin mensaje propio da «Revisá los datos.»', () => {
    const rechazo = new EntradaRechazada('Entrada rechazada.', null, [], [
      { campo: 'contrasena_actual', codigo: null, mensaje: 'No puede estar vacío.' },
    ])

    expect(erroresDeCambioPropio(rechazo).aviso).toBe('Revisá los datos.')
    expect(erroresDeRestablecimiento(rechazo).aviso).toBe('Revisá los datos.')
  })
})
