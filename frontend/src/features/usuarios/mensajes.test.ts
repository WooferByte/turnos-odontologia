import { describe, expect, it } from 'vitest'
import { EntradaRechazada } from '../../shared/api/errores'
import { erroresDelPanel } from './mensajes'

describe('mensajes de la pantalla de usuarios', () => {
  it('U19: un 422 de un campo sin mensaje propio da «Revisá los datos del usuario.»', () => {
    const rechazo = new EntradaRechazada(
      'Entrada rechazada.',
      null,
      [],
      [{ campo: 'otro', codigo: null, mensaje: 'Campo no permitido.' }],
    )

    expect(erroresDelPanel(rechazo)).toEqual({
      email: null,
      contrasena: null,
      roles: null,
      aviso: 'Revisá los datos del usuario.',
    })
  })

  it('U19: un 422 con errores del email y de los roles los muestra debajo de cada campo y sin aviso', () => {
    const rechazo = new EntradaRechazada(
      'Entrada rechazada.',
      null,
      [],
      [
        { campo: 'email', codigo: null, mensaje: 'Formato.' },
        { campo: 'roles', codigo: null, mensaje: 'Vacía.' },
      ],
    )

    expect(erroresDelPanel(rechazo)).toEqual({
      email: 'Ingresá un email válido.',
      contrasena: null,
      roles: 'Elegí al menos un rol.',
      aviso: null,
    })
  })

  it('U19: un 422 sin errores de campo también da «Revisá los datos del usuario.»', () => {
    const rechazo = new EntradaRechazada('Entrada rechazada.', null)

    expect(erroresDelPanel(rechazo).aviso).toBe('Revisá los datos del usuario.')
  })
})
