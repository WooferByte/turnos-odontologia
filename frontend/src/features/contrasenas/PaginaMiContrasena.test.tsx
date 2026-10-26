import { cleanup, render, screen, waitFor } from '@testing-library/react'
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
const RUTA = '/api/auth/cambiar-contrasena'
const AVISO_DE_CAMBIADA = 'Contraseña cambiada. Tus otras sesiones se cerraron.'
const MENSAJE_ACTUAL_INCORRECTA = 'La contraseña actual no es correcta (RN-AU-09).'
const MENSAJE_CONTRASENA_CORTA = 'La contraseña debe tener de 10 caracteres a 72 bytes (RN-AU-07).'
const MENSAJE_DE_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'
const AVISO_SESION_TERMINADA = 'Tu sesión terminó. Iniciá sesión de nuevo.'

function LugarActual() {
  const ubicacion = useLocation()
  return <p data-testid="lugar">{ubicacion.pathname}</p>
}

/** Monta la aplicación con una sesión guardada, ya dentro del panel. */
async function abrirPanel(servidor: ServidorFalso, email = EMAIL_RECEPCIONISTA, ruta = '/panel') {
  sessionStorage.setItem(CLAVE_DE_SESION, JSON.stringify({ refresh: servidor.emitirSesion(email).refresh }))
  render(
    <MemoryRouter initialEntries={[ruta]}>
      <LugarActual />
      <App fetch={servidor.fetch} />
    </MemoryRouter>,
  )
  await screen.findByText('Panel del consultorio')
  return userEvent.setup()
}

type Usuario = ReturnType<typeof userEvent.setup>

async function irAMiContrasena(usuario: Usuario) {
  await usuario.click(screen.getByRole('link', { name: 'Mi contraseña' }))
  await screen.findByRole('heading', { name: 'Mi contraseña' })
}

function campo(nombre: string): HTMLInputElement {
  return screen.getByLabelText<HTMLInputElement>(nombre)
}

interface Datos {
  actual?: string
  nueva?: string
  repeticion?: string
}

async function completar(usuario: Usuario, datos: Datos = {}) {
  await usuario.type(campo('Contraseña actual'), datos.actual ?? CONTRASENA_DEMO)
  await usuario.type(campo('Contraseña nueva'), datos.nueva ?? NUEVA)
  await usuario.type(campo('Repetir contraseña nueva'), datos.repeticion ?? datos.nueva ?? NUEVA)
}

async function cambiar(usuario: Usuario, datos: Datos = {}) {
  await completar(usuario, datos)
  await usuario.click(screen.getByRole('button', { name: 'Cambiar contraseña' }))
}

function valores(): string[] {
  return ['Contraseña actual', 'Contraseña nueva', 'Repetir contraseña nueva'].map((n) => campo(n).value)
}

describe('«Mi contraseña»: lo principal', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-093 CA-7: la recepcionista cambia la suya', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor)
    await irAMiContrasena(usuario)

    await cambiar(usuario)

    expect((await screen.findByRole('status')).textContent).toContain(AVISO_DE_CAMBIADA)
    expect(servidor.llamadas('POST', RUTA)).toBe(1)
    expect(servidor.cuerpos('POST', RUTA)).toEqual([{ contrasena_actual: CONTRASENA_DEMO, contrasena_nueva: NUEVA }])
    expect(valores()).toEqual(['', '', ''])
    expect(screen.getByTestId('lugar').textContent).toBe('/panel/contrasena')
    expect(servidor.contrasenaDe(EMAIL_RECEPCIONISTA)).toBe(NUEVA)
  })

  it('US-093 CA-7: la siguiente petición usa el token nuevo sin renovar', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor)
    await irAMiContrasena(usuario)
    const renovacionesAlAbrir = servidor.peticiones('/api/auth/refresh')
    await cambiar(usuario)
    await screen.findByRole('status')

    await usuario.click(screen.getByRole('link', { name: 'Prestaciones' }))

    await screen.findByRole('table')
    expect(servidor.llamadas('GET', '/api/prestaciones')).toBe(1)
    expect(servidor.peticiones('/api/auth/refresh')).toBe(renovacionesAlAbrir)
    expect(screen.getByTestId('lugar').textContent).toBe('/panel/prestaciones')
  })
})

describe('«Mi contraseña»: bordes y errores', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-093 CA-7: la contraseña actual incorrecta se muestra debajo de la actual', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor)
    await irAMiContrasena(usuario)
    const renovacionesAlAbrir = servidor.peticiones('/api/auth/refresh')

    await cambiar(usuario, { actual: 'no-es-la-actual-2026' })

    const error = await screen.findByText(MENSAJE_ACTUAL_INCORRECTA)
    expect(campo('Contraseña actual').closest('.campo')?.contains(error)).toBe(true)
    expect(campo('Contraseña actual').getAttribute('aria-invalid')).toBe('true')
    expect(servidor.peticiones('/api/auth/refresh')).toBe(renovacionesAlAbrir)
    expect(screen.getByTestId('lugar').textContent).toBe('/panel/contrasena')
    expect(valores()).toEqual(['no-es-la-actual-2026', NUEVA, NUEVA])
  })

  it('US-093 CA-9: la contraseña nueva corta se muestra debajo de la nueva', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor)
    await irAMiContrasena(usuario)

    await cambiar(usuario, { nueva: 'corta-123' })

    const error = await screen.findByText(MENSAJE_CONTRASENA_CORTA)
    expect(servidor.cuerpos('POST', RUTA)).toEqual([
      { contrasena_actual: CONTRASENA_DEMO, contrasena_nueva: 'corta-123' },
    ])
    expect(campo('Contraseña nueva').closest('.campo')?.contains(error)).toBe(true)
    expect(servidor.contrasenaDe(EMAIL_RECEPCIONISTA)).toBe(CONTRASENA_DEMO)
  })

  it('US-093 CA-7: la repetición distinta no manda nada', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor)
    await irAMiContrasena(usuario)

    await cambiar(usuario, { nueva: NUEVA, repeticion: 'clave-nueva-2027' })

    const error = await screen.findByText('Las contraseñas nuevas no coinciden.')
    expect(campo('Repetir contraseña nueva').closest('.campo')?.contains(error)).toBe(true)
    expect(servidor.llamadas('POST', RUTA)).toBe(0)
  })

  it('US-093 CA-7: un campo vacío no manda nada', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor)
    await irAMiContrasena(usuario)

    await usuario.type(campo('Contraseña actual'), CONTRASENA_DEMO)
    await usuario.type(campo('Contraseña nueva'), NUEVA)
    await usuario.click(screen.getByRole('button', { name: 'Cambiar contraseña' }))

    expect(servidor.llamadas('POST', RUTA)).toBe(0)
  })

  it('US-093 CA-7: pulsar dos veces manda un solo pedido', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor)
    await irAMiContrasena(usuario)
    const liberar = servidor.retener(RUTA)
    await completar(usuario)

    await usuario.click(screen.getByRole('button', { name: 'Cambiar contraseña' }))
    const espera = screen.getByRole<HTMLButtonElement>('button', { name: 'Cambiando…' })
    await usuario.click(espera)

    expect(espera.disabled).toBe(true)
    expect(servidor.llamadas('POST', RUTA)).toBe(1)
    liberar()
    expect((await screen.findByRole('status')).textContent).toContain(AVISO_DE_CAMBIADA)
    expect(servidor.llamadas('POST', RUTA)).toBe(1)
  })

  it('US-093 CA-7: sin conexión, el aviso de conexión conserva lo escrito', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor)
    await irAMiContrasena(usuario)
    await completar(usuario)
    servidor.caerse()

    await usuario.click(screen.getByRole('button', { name: 'Cambiar contraseña' }))

    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_DE_CONEXION)
    expect(valores()).toEqual([CONTRASENA_DEMO, NUEVA, NUEVA])
    expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Cambiar contraseña' }).disabled).toBe(false)
  })

  it('US-093 CA-7: al salir y volver, los campos están vacíos', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor)
    await irAMiContrasena(usuario)
    await completar(usuario)

    await usuario.click(screen.getByRole('link', { name: 'Prestaciones' }))
    await screen.findByRole('table')
    await irAMiContrasena(usuario)

    expect(valores()).toEqual(['', '', ''])
    expect(servidor.llamadas('POST', RUTA)).toBe(0)
  })

  it('US-093 CA-7: todos los roles ven «Mi contraseña»', async () => {
    const catalogo = [...USUARIOS_DE_PARTIDA, USUARIO_DUENO]
    for (const email of [EMAIL_ACTIVA, EMAIL_RECEPCIONISTA, EMAIL_DUENO]) {
      await abrirPanel(crearServidorFalso({ usuarios: catalogo }), email)

      expect(screen.getByRole('link', { name: 'Mi contraseña' }).getAttribute('href')).toBe('/panel/contrasena')

      cleanup()
      sessionStorage.clear()
    }
  })

  it('US-093 CA-7: recargar después de cambiarla conserva la sesión', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor)
    await irAMiContrasena(usuario)
    await cambiar(usuario)
    await screen.findByRole('status')
    cleanup()

    render(
      <MemoryRouter initialEntries={['/panel']}>
        <LugarActual />
        <App fetch={servidor.fetch} />
      </MemoryRouter>,
    )

    await screen.findByText('Panel del consultorio')
    expect(screen.queryByText(AVISO_SESION_TERMINADA)).toBeNull()
    expect(screen.getByTestId('lugar').textContent).toBe('/panel')
  })

  it('US-092 CA-1: una sesión irrenovable al cambiar la propia', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor)
    await irAMiContrasena(usuario)
    await completar(usuario)
    servidor.vencerAccess()
    servidor.invalidarRefresh()

    await usuario.click(screen.getByRole('button', { name: 'Cambiar contraseña' }))

    await waitFor(() => expect(screen.getByTestId('lugar').textContent).toBe('/ingresar'))
    expect(screen.getByText(AVISO_SESION_TERMINADA)).toBeDefined()
    expect(screen.queryByText(MENSAJE_DE_CONEXION)).toBeNull()
    expect(servidor.contrasenaDe(EMAIL_RECEPCIONISTA)).toBe(CONTRASENA_DEMO)
  })
})
