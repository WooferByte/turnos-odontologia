import { describe, expect, it } from 'vitest'
import { crearClienteHttp } from '../../shared/api/clienteHttp'
import { EntradaRechazada, PermisoInsuficiente, RecursoInexistente, ReglaRechazada } from '../../shared/api/errores'
import { crearSesion } from '../../shared/api/sesion'
import {
  EMAIL_ACTIVA,
  EMAIL_RECEPCIONISTA,
  crearServidorFalso,
  type ServidorFalso,
} from '../../test/servidorFalso'
import { crearApiUsuarios, rolesCambiados } from './apiUsuarios'

function apiConSesion(servidor: ServidorFalso, email: string = EMAIL_ACTIVA) {
  const sesion = crearSesion(null)
  const { access, refresh } = servidor.emitirSesion(email)
  sesion.guardar(access, refresh)
  const cliente = crearClienteHttp({ fetch: servidor.fetch, sesion })
  return crearApiUsuarios(cliente.pedidoDelPanel)
}

const CONTRASENA_VALIDA = 'clave-ficticia-2026'

describe('apiUsuarios', () => {
  it('US-093 CA-1: listar devuelve los usuarios en orden de id', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor)

    const lista = await api.listarUsuarios()

    expect(lista.map((u) => u.id)).toEqual([1, 2, 3])
    expect(lista[1]).toEqual({ id: 2, email: EMAIL_RECEPCIONISTA, roles: ['recepcionista'], activo: true })
    expect(lista[2]?.activo).toBe(false)
    expect(servidor.llamadas('GET', '/api/usuarios')).toBe(1)
  })

  it('US-093 CA-1: crear devuelve el usuario nuevo', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor)

    const nuevo = await api.crearUsuario({
      email: 'turnos@consultorio-demo.test',
      contrasena: CONTRASENA_VALIDA,
      roles: ['recepcionista'],
    })

    expect(nuevo).toEqual({ id: 4, email: 'turnos@consultorio-demo.test', roles: ['recepcionista'], activo: true })
    expect(servidor.cuerpos('POST', '/api/usuarios')).toEqual([
      { email: 'turnos@consultorio-demo.test', contrasena: CONTRASENA_VALIDA, roles: ['recepcionista'] },
    ])
    expect(servidor.usuariosActuales()).toHaveLength(4)
  })

  it('US-093 CA-2: email repetido levanta ReglaRechazada con RN-AU-08', async () => {
    const api = apiConSesion(crearServidorFalso())

    const error = await api
      .crearUsuario({ email: EMAIL_RECEPCIONISTA, contrasena: CONTRASENA_VALIDA, roles: ['recepcionista'] })
      .catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ReglaRechazada)
    expect((error as ReglaRechazada).codigo).toBe('RN-AU-08')
  })

  it('US-093 CA-9: contraseña inicial corta levanta EntradaRechazada con el error de campo RN-AU-07', async () => {
    const api = apiConSesion(crearServidorFalso())

    const error = await api
      .crearUsuario({ email: 'turnos@consultorio-demo.test', contrasena: 'corta-123', roles: ['recepcionista'] })
      .catch((e: unknown) => e)

    expect(error).toBeInstanceOf(EntradaRechazada)
    const rechazo = error as EntradaRechazada
    expect(rechazo.codigos).toEqual(['RN-AU-07'])
    expect(rechazo.errores.map((e) => [e.campo, e.codigo])).toEqual([['contrasena', 'RN-AU-07']])
  })

  it('US-093 CA-1: editar manda solo roles', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor)

    const editado = await api.editarUsuario(2, { roles: ['recepcionista', 'dueno'] })

    expect(servidor.cuerpos('PATCH', '/api/usuarios/2')).toEqual([{ roles: ['recepcionista', 'dueno'] }])
    expect(editado).toEqual({ id: 2, email: EMAIL_RECEPCIONISTA, roles: ['recepcionista', 'dueno'], activo: true })
  })

  it('US-093 CA-1: rolesCambiados no cuenta el orden', () => {
    expect(rolesCambiados(['odontologo', 'dueno'], ['dueno', 'odontologo'])).toBe(false)
    expect(rolesCambiados(['recepcionista'], ['recepcionista', 'dueno'])).toBe(true)
    expect(rolesCambiados(['odontologo', 'dueno'], ['dueno'])).toBe(true)
    expect(rolesCambiados(['recepcionista'], ['dueno'])).toBe(true)
  })

  it('US-093 CA-5: desactivarse levanta ReglaRechazada con RN-AU-06', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor)

    const error = await api.editarUsuario(1, { activo: false }).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ReglaRechazada)
    expect((error as ReglaRechazada).codigo).toBe('RN-AU-06')
    expect(servidor.usuariosActuales()[0]?.activo).toBe(true)
  })

  it('US-093 CA-1: la recepcionista que lista recibe PermisoInsuficiente', async () => {
    const api = apiConSesion(crearServidorFalso(), EMAIL_RECEPCIONISTA)

    const error = await api.listarUsuarios().catch((e: unknown) => e)

    expect(error).toBeInstanceOf(PermisoInsuficiente)
    expect((error as PermisoInsuficiente).codigo).toBe('RN-AU-05')
  })

  it('US-093 CA-3: id inexistente levanta RecursoInexistente con RN-GL-04', async () => {
    const api = apiConSesion(crearServidorFalso())

    const error = await api.editarUsuario(99, { activo: false }).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(RecursoInexistente)
    expect((error as RecursoInexistente).codigo).toBe('RN-GL-04')
  })

  it('US-093 CA-1: sin permiso y con contraseña corta levanta PermisoInsuficiente', async () => {
    const servidor = crearServidorFalso()
    const api = apiConSesion(servidor, EMAIL_RECEPCIONISTA)

    const error = await api
      .crearUsuario({ email: 'turnos@consultorio-demo.test', contrasena: 'corta-123', roles: ['recepcionista'] })
      .catch((e: unknown) => e)

    expect(error).toBeInstanceOf(PermisoInsuficiente)
    expect(error).not.toBeInstanceOf(EntradaRechazada)
    expect(servidor.usuariosActuales()).toHaveLength(3)
  })
})
