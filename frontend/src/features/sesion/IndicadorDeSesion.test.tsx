import { act, cleanup, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { App } from '../../App'
import { CLAVE_DE_SESION } from '../../shared/api/sesion'
import {
  CONTRASENA_DEMO,
  CONTRASENA_FICTICIA,
  EMAIL_ACTIVA,
  EMAIL_RECEPCIONISTA,
  PRESTACIONES_DE_PARTIDA,
  crearServidorFalso,
  type ServidorFalso,
} from '../../test/servidorFalso'

const RUTA = '/api/auth/yo'
const ROLES_DE_LA_ODONTOLOGA = 'Odontólogo · Dueño'
const AVISO_SESION_TERMINADA = 'Tu sesión terminó. Iniciá sesión de nuevo.'

type Usuario = ReturnType<typeof userEvent.setup>

function montar(ruta: string, servidor: ServidorFalso) {
  render(
    <MemoryRouter initialEntries={[ruta]}>
      <App fetch={servidor.fetch} />
    </MemoryRouter>,
  )
  return userEvent.setup()
}

async function ingresar(usuario: Usuario, email: string, contrasena: string) {
  await usuario.type(screen.getByLabelText('Email'), email)
  await usuario.type(screen.getByLabelText('Contraseña'), contrasena)
  await usuario.click(screen.getByRole('button', { name: 'Ingresar' }))
}

function encabezado(): HTMLElement {
  return screen.getByRole('banner')
}

/** Da tiempo a que una respuesta retenida y liberada llegue a la pantalla (sin temporizadores falsos). */
async function dejarPasarElTiempo(): Promise<void> {
  await act(async () => {
    await new Promise<void>((resolver) => setTimeout(resolver, 50))
  })
}

async function cerrarSesion(usuario: Usuario) {
  await usuario.click(within(encabezado()).getByRole('button', { name: 'Cerrar sesión' }))
  await screen.findByRole('heading', { name: 'Turnos Odontológicos AR' })
}

describe('IndicadorDeSesion: el usuario en el encabezado', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('SES-4a: después de iniciar sesión el encabezado muestra el email y los roles', async () => {
    const servidor = crearServidorFalso()
    const usuario = montar('/ingresar', servidor)

    await ingresar(usuario, EMAIL_ACTIVA, CONTRASENA_FICTICIA)

    await screen.findByRole('banner')
    const email = await within(encabezado()).findByText(EMAIL_ACTIVA)
    const roles = within(encabezado()).getByText(ROLES_DE_LA_ODONTOLOGA)
    const cerrar = within(encabezado()).getByRole('button', { name: 'Cerrar sesión' })
    expect(cerrar.previousElementSibling?.contains(email)).toBe(true)
    expect(cerrar.previousElementSibling?.contains(roles)).toBe(true)
    expect(servidor.llamadas('GET', RUTA)).toBe(1)
  })

  it('SES-4b: navegar entre pantallas no vuelve a pedir el usuario', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = montar('/ingresar', servidor)
    await ingresar(usuario, EMAIL_RECEPCIONISTA, CONTRASENA_DEMO)
    await within(await screen.findByRole('banner')).findByText(EMAIL_RECEPCIONISTA)
    expect(within(encabezado()).getByText('Recepcionista')).toBeDefined()

    for (const [enlace, titulo] of [
      ['Prestaciones', 'Prestaciones'],
      ['Horario', 'Horario de atención'],
      ['Bloqueos', 'Bloqueos'],
      ['Mi contraseña', 'Mi contraseña'],
    ]) {
      await usuario.click(within(encabezado()).getByRole('link', { name: enlace }))
      await screen.findByRole('heading', { name: titulo })
      expect(within(encabezado()).getByText(EMAIL_RECEPCIONISTA)).toBeDefined()
      expect(within(encabezado()).getByText('Recepcionista')).toBeDefined()
    }

    expect(servidor.llamadas('GET', RUTA)).toBe(1)
  })

  it('SES-4c: al recargar la pestaña el usuario se muestra después de renovar', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    sessionStorage.setItem(CLAVE_DE_SESION, JSON.stringify({ refresh: servidor.emitirSesion(EMAIL_ACTIVA).refresh }))
    const liberar = servidor.retener(RUTA)

    montar('/panel/prestaciones', servidor)

    await waitFor(() => expect(servidor.llamadas('GET', RUTA)).toBe(1))
    const pedidas = servidor.rutasPedidas()
    expect(pedidas.indexOf('/api/auth/refresh')).toBeGreaterThanOrEqual(0)
    expect(pedidas.indexOf('/api/auth/refresh')).toBeLessThan(pedidas.indexOf(RUTA))
    expect(within(encabezado()).queryByText(EMAIL_ACTIVA)).toBeNull()
    liberar()
    expect(await within(encabezado()).findByText(EMAIL_ACTIVA)).toBeDefined()
    expect(within(encabezado()).getByText(ROLES_DE_LA_ODONTOLOGA)).toBeDefined()
    expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(1)
  })

  it('SES-4d: otro usuario en la misma pestaña ve sus propios datos', async () => {
    const servidor = crearServidorFalso()
    const usuario = montar('/ingresar', servidor)
    await ingresar(usuario, EMAIL_ACTIVA, CONTRASENA_FICTICIA)
    await within(await screen.findByRole('banner')).findByText(EMAIL_ACTIVA)

    await cerrarSesion(usuario)
    const liberar = servidor.retener(RUTA)
    await ingresar(usuario, EMAIL_RECEPCIONISTA, CONTRASENA_DEMO)

    await waitFor(() => expect(servidor.llamadas('GET', RUTA)).toBe(2))
    await screen.findByRole('banner')
    expect(screen.queryByText(EMAIL_ACTIVA)).toBeNull()
    expect(screen.queryByText(ROLES_DE_LA_ODONTOLOGA)).toBeNull()
    liberar()
    await within(encabezado()).findByText(EMAIL_RECEPCIONISTA)
    expect(within(encabezado()).getByText('Recepcionista')).toBeDefined()
    expect(screen.queryByText(EMAIL_ACTIVA)).toBeNull()
    expect(screen.queryByText(ROLES_DE_LA_ODONTOLOGA)).toBeNull()
    expect(servidor.llamadas('GET', RUTA)).toBe(2)
  })

  it('SES-4e: una respuesta tardía después de cerrar sesión no se muestra', async () => {
    const servidor = crearServidorFalso()
    const liberar = servidor.retener(RUTA)
    const usuario = montar('/ingresar', servidor)
    await ingresar(usuario, EMAIL_ACTIVA, CONTRASENA_FICTICIA)
    await waitFor(() => expect(servidor.llamadas('GET', RUTA)).toBe(1))

    await cerrarSesion(usuario)
    liberar()
    await dejarPasarElTiempo()

    expect(screen.queryByText(EMAIL_ACTIVA)).toBeNull()
    expect(screen.queryByText(ROLES_DE_LA_ODONTOLOGA)).toBeNull()
  })

  it('SES-5b: un 401 con el refresh vigente renueva y muestra el usuario', async () => {
    const servidor = crearServidorFalso()
    const liberar = servidor.retener(RUTA)
    const usuario = montar('/ingresar', servidor)
    await ingresar(usuario, EMAIL_ACTIVA, CONTRASENA_FICTICIA)
    await waitFor(() => expect(servidor.llamadas('GET', RUTA)).toBe(1))

    servidor.vencerAccess()
    liberar()

    expect(await within(encabezado()).findByText(EMAIL_ACTIVA)).toBeDefined()
    expect(within(encabezado()).getByText(ROLES_DE_LA_ODONTOLOGA)).toBeDefined()
    expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(1)
    expect(servidor.llamadas('GET', RUTA)).toBe(2)
    expect(screen.queryByText(AVISO_SESION_TERMINADA)).toBeNull()
  })

  it('SES-5a: un 401 sin renovación posible vuelve al inicio de sesión', async () => {
    const servidor = crearServidorFalso()
    const liberar = servidor.retener(RUTA)
    const usuario = montar('/ingresar', servidor)
    await ingresar(usuario, EMAIL_RECEPCIONISTA, CONTRASENA_DEMO)
    await waitFor(() => expect(servidor.llamadas('GET', RUTA)).toBe(1))

    servidor.vencerAccess()
    servidor.invalidarRefresh()
    liberar()

    expect((await screen.findByRole('status')).textContent).toContain(AVISO_SESION_TERMINADA)
    expect(screen.getByRole('heading', { name: 'Turnos Odontológicos AR' })).toBeDefined()
    expect(screen.queryByRole('button', { name: 'Cerrar sesión' })).toBeNull()
    expect(screen.queryByRole('navigation', { name: 'Principal' })).toBeNull()
    expect(screen.queryByText(EMAIL_RECEPCIONISTA)).toBeNull()
    expect(sessionStorage.getItem(CLAVE_DE_SESION)).toBeNull()
    expect(servidor.llamadas('GET', RUTA)).toBe(1)
  })
})

/** Entra con la odontóloga y comprueba lo común de los escenarios de falla: sin indicador, sin aviso, una sola llamada. */
async function entrarSinIndicador(servidor: ServidorFalso): Promise<Usuario> {
  const usuario = montar('/ingresar', servidor)
  await ingresar(usuario, EMAIL_ACTIVA, CONTRASENA_FICTICIA)
  await screen.findByRole('banner')
  await waitFor(() => expect(servidor.llamadas('GET', RUTA)).toBe(1))
  await dejarPasarElTiempo()
  expect(within(encabezado()).queryByText(EMAIL_ACTIVA)).toBeNull()
  expect(within(encabezado()).queryByText(ROLES_DE_LA_ODONTOLOGA)).toBeNull()
  expect(within(encabezado()).getByRole('button', { name: 'Cerrar sesión' })).toBeDefined()
  expect(screen.queryByRole('alert')).toBeNull()
  expect(screen.queryByRole('status')).toBeNull()
  return usuario
}

async function prestacionesCargan(usuario: Usuario) {
  await usuario.click(within(encabezado()).getByRole('link', { name: 'Prestaciones' }))
  expect(await screen.findByText('Consulta / control')).toBeDefined()
}

describe('IndicadorDeSesion: otras fallas no interrumpen el panel', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('SES-4f: sin conexión el panel sigue sin el indicador', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    servidor.fallarRuta(RUTA, 'red')

    const usuario = await entrarSinIndicador(servidor)

    await prestacionesCargan(usuario)
    expect(screen.queryByRole('alert')).toBeNull()
    expect(servidor.llamadas('GET', RUTA)).toBe(1)
    await cerrarSesion(usuario)
  })

  it('SES-4g: con un error del servidor el panel sigue sin el indicador', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    servidor.fallarRuta(RUTA, 500)

    const usuario = await entrarSinIndicador(servidor)

    await prestacionesCargan(usuario)
    expect(screen.queryByRole('alert')).toBeNull()
    expect(servidor.llamadas('GET', RUTA)).toBe(1)
  })

  it('SES-4h: con 403 el panel sigue sin el indicador', async () => {
    const servidor = crearServidorFalso()
    servidor.quitarPermiso(EMAIL_ACTIVA)

    const usuario = await entrarSinIndicador(servidor)

    await cerrarSesion(usuario)
    expect(servidor.llamadas('GET', RUTA)).toBe(1)
  })

  it('SES-4i: con una respuesta de otra forma el panel sigue sin el indicador', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    servidor.fallarRuta(RUTA, { cuerpo: { email: EMAIL_ACTIVA, roles: ['administrador'] } })

    const usuario = await entrarSinIndicador(servidor)

    await prestacionesCargan(usuario)
    expect(screen.queryByText('administrador')).toBeNull()
    expect(servidor.llamadas('GET', RUTA)).toBe(1)
  })
})
