import { cleanup, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { App } from '../../App'
import { CLAVE_DE_SESION } from '../../shared/api/sesion'
import {
  CONTRASENA_DEMO,
  EMAIL_ACTIVA,
  EMAIL_DUENO,
  EMAIL_RECEPCIONISTA,
  PRESTACIONES_DE_PARTIDA,
  USUARIOS_DE_PARTIDA,
  USUARIO_DUENO,
  crearServidorFalso,
  type ServidorFalso,
} from '../../test/servidorFalso'

const NUEVA = 'clave-nueva-2026'
const RUTA = '/api/usuarios/2/restablecer-contrasena'
const AVISO_DE_RESTABLECIDA = `Contraseña restablecida. Se cerraron las sesiones de ${EMAIL_RECEPCIONISTA}.`
const MENSAJE_CONTRASENA_CORTA = 'La contraseña debe tener de 10 caracteres a 72 bytes (RN-AU-07).'
const MENSAJE_DE_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'
const AVISO_SESION_TERMINADA = 'Tu sesión terminó. Iniciá sesión de nuevo.'

function LugarActual() {
  const ubicacion = useLocation()
  return <p data-testid="lugar">{ubicacion.pathname}</p>
}

async function abrirUsuarios(servidor: ServidorFalso, email = EMAIL_ACTIVA) {
  sessionStorage.setItem(CLAVE_DE_SESION, JSON.stringify({ refresh: servidor.emitirSesion(email).refresh }))
  render(
    <MemoryRouter initialEntries={['/panel/usuarios']}>
      <LugarActual />
      <App fetch={servidor.fetch} />
    </MemoryRouter>,
  )
  await screen.findByRole('table')
  return userEvent.setup()
}

type Usuario = ReturnType<typeof userEvent.setup>

function filasDeDatos(): string[] {
  return within(screen.getByRole('table'))
    .getAllByRole<HTMLTableRowElement>('row')
    .slice(1)
    .map((fila) => fila.textContent ?? '')
}

async function abrirRestablecer(usuario: Usuario, email = EMAIL_RECEPCIONISTA) {
  await usuario.click(screen.getByRole('button', { name: `Restablecer contraseña ${email}` }))
}

function campo(): HTMLInputElement {
  return screen.getByLabelText<HTMLInputElement>('Contraseña nueva')
}

async function restablecer(usuario: Usuario, contrasena: string, email = EMAIL_RECEPCIONISTA) {
  await abrirRestablecer(usuario, email)
  await usuario.type(campo(), contrasena)
  await usuario.click(screen.getByRole('button', { name: 'Guardar' }))
}

describe('Restablecer contraseña desde la fila: lo principal', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-093 CA-6: la odontóloga restablece la contraseña de la recepcionista', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirUsuarios(servidor)
    const antes = filasDeDatos()

    await restablecer(usuario, NUEVA)

    expect((await screen.findByRole('status')).textContent).toContain(AVISO_DE_RESTABLECIDA)
    expect(servidor.llamadas('POST', RUTA)).toBe(1)
    expect(servidor.cuerpos('POST', RUTA)).toEqual([{ contrasena: NUEVA }])
    expect(screen.queryByRole('complementary')).toBeNull()
    expect(filasDeDatos()).toEqual(antes)

    await abrirRestablecer(usuario)

    expect(campo().value).toBe('')
  })

  it('US-093 CA-9: la contraseña corta se muestra debajo del campo', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirUsuarios(servidor)

    await restablecer(usuario, 'corta-123')

    const error = await screen.findByText(MENSAJE_CONTRASENA_CORTA)
    expect(servidor.cuerpos('POST', RUTA)).toEqual([{ contrasena: 'corta-123' }])
    expect(campo().closest('.campo')?.contains(error)).toBe(true)
    expect(campo().getAttribute('aria-invalid')).toBe('true')
    expect(campo().value).toBe('corta-123')
    expect(screen.getByRole('complementary')).toBeDefined()
    expect(servidor.contrasenaDe(EMAIL_RECEPCIONISTA)).toBe(CONTRASENA_DEMO)
  })
})

describe('Restablecer contraseña desde la fila: bordes y errores', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-093 CA-6: la odontóloga no restablece la propia', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirUsuarios(servidor)

    await restablecer(usuario, NUEVA, EMAIL_ACTIVA)

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain('Tu propia contraseña se cambia desde «Mi contraseña» (RN-AU-10).')
    expect(within(screen.getByRole('complementary')).getByRole('alert')).toBe(aviso)
    expect(campo().value).toBe(NUEVA)
    expect(servidor.contrasenaDe(EMAIL_ACTIVA)).not.toBe(NUEVA)
    expect(screen.getByTestId('lugar').textContent).toBe('/panel/usuarios')
  })

  it('US-093 CA-6: el dueño ve el rechazo sin perder la sesión', async () => {
    const catalogo = [...USUARIOS_DE_PARTIDA, USUARIO_DUENO]
    const servidor = crearServidorFalso({ usuarios: catalogo })
    const usuario = await abrirUsuarios(servidor, EMAIL_DUENO)
    const renovacionesAlAbrir = servidor.peticiones('/api/auth/refresh')

    await restablecer(usuario, NUEVA)

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain('Tu usuario no tiene permiso para modificar usuarios (RN-AU-05).')
    expect(campo().value).toBe(NUEVA)
    expect(servidor.peticiones('/api/auth/refresh')).toBe(renovacionesAlAbrir)
    expect(screen.getByTestId('lugar').textContent).toBe('/panel/usuarios')
  })

  it('US-093 CA-6: Cancelar, Cerrar y el campo vacío no piden nada', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirUsuarios(servidor)

    await abrirRestablecer(usuario)
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))
    await usuario.type(campo(), NUEVA)
    await usuario.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(screen.queryByRole('complementary')).toBeNull()
    await abrirRestablecer(usuario)
    expect(campo().value).toBe('')
    await usuario.type(campo(), NUEVA)
    await usuario.click(screen.getByRole('button', { name: 'Cerrar' }))
    expect(screen.queryByRole('complementary')).toBeNull()
    await abrirRestablecer(usuario)

    expect(campo().value).toBe('')
    expect(servidor.llamadas('POST', RUTA)).toBe(0)
  })

  it('US-093 CA-6: pulsar «Guardar» dos veces manda un solo pedido', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirUsuarios(servidor)
    const liberar = servidor.retener(RUTA)
    await abrirRestablecer(usuario)
    await usuario.type(campo(), NUEVA)

    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))
    const espera = screen.getByRole<HTMLButtonElement>('button', { name: 'Guardando…' })
    await usuario.click(espera)

    expect(espera.disabled).toBe(true)
    expect(servidor.llamadas('POST', RUTA)).toBe(1)
    liberar()
    expect((await screen.findByRole('status')).textContent).toContain(AVISO_DE_RESTABLECIDA)
    expect(servidor.llamadas('POST', RUTA)).toBe(1)
  })

  it('US-093 CA-6: sin conexión, el aviso de conexión conserva lo escrito', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirUsuarios(servidor)
    await abrirRestablecer(usuario)
    await usuario.type(campo(), NUEVA)
    servidor.caerse()

    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    expect((await within(screen.getByRole('complementary')).findByRole('alert')).textContent).toContain(
      MENSAJE_DE_CONEXION,
    )
    expect(campo().value).toBe(NUEVA)
    expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Guardar' }).disabled).toBe(false)
  })

  it('US-093 CA-6: un usuario que ya no existe cierra el panel y recarga la lista', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirUsuarios(servidor)
    await abrirRestablecer(usuario)
    await usuario.type(campo(), NUEVA)
    servidor.quitarUsuario(2)

    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    expect((await screen.findByRole('alert')).textContent).toContain('El usuario ya no existe (RN-GL-04).')
    expect(screen.queryByRole('complementary')).toBeNull()
    await waitFor(() => expect(servidor.llamadas('GET', '/api/usuarios')).toBe(2))
    await waitFor(() => expect(filasDeDatos()).toHaveLength(2))
  })

  it('US-092 CA-1: una sesión irrenovable al restablecer', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirUsuarios(servidor)
    await abrirRestablecer(usuario)
    await usuario.type(campo(), NUEVA)
    servidor.vencerAccess()
    servidor.invalidarRefresh()

    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => expect(screen.getByTestId('lugar').textContent).toBe('/ingresar'))
    expect(screen.getByText(AVISO_SESION_TERMINADA)).toBeDefined()
    expect(screen.queryByText(MENSAJE_DE_CONEXION)).toBeNull()
    expect(servidor.contrasenaDe(EMAIL_RECEPCIONISTA)).toBe(CONTRASENA_DEMO)
  })
})
