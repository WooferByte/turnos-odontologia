import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { App } from '../../App'
import {
  CONTRASENA_FICTICIA,
  EMAIL_ACTIVA,
  EMAIL_INACTIVA,
  crearServidorFalso,
  type ServidorFalso,
} from '../../test/servidorFalso'

const MENSAJE_GENERICO = 'El email o la contraseña no son correctos.'
const MENSAJE_DE_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'

type Usuario = ReturnType<typeof userEvent.setup>

async function ingresar(usuario: Usuario, email: string, contrasena: string) {
  await usuario.type(screen.getByLabelText('Email'), email)
  await usuario.type(screen.getByLabelText('Contraseña'), contrasena)
  await usuario.click(screen.getByRole('button', { name: 'Ingresar' }))
}

function montar(ruta: string, servidor: ServidorFalso) {
  render(
    <MemoryRouter initialEntries={[ruta]}>
      <App fetch={servidor.fetch} />
    </MemoryRouter>,
  )
  return userEvent.setup()
}

function expectEntre(antes: Element, medio: Element, despues: Element): void {
  expect(antes.compareDocumentPosition(medio) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  expect(medio.compareDocumentPosition(despues) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
}

describe('PaginaIngreso', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-090 CA-1: credenciales válidas llevan al panel', async () => {
    const servidor = crearServidorFalso()
    const usuario = montar('/ingresar', servidor)

    await usuario.type(screen.getByLabelText('Email'), EMAIL_ACTIVA)
    await usuario.type(screen.getByLabelText('Contraseña'), CONTRASENA_FICTICIA)
    await usuario.click(screen.getByRole('button', { name: 'Ingresar' }))

    expect(await screen.findByText('Panel del consultorio')).toBeDefined()
    expect(screen.getByRole('button', { name: 'Cerrar sesión' })).toBeDefined()
    expect(servidor.peticiones('/api/auth/login')).toBe(1)
  })

  it('US-090 CA-2: email inexistente muestra el mensaje genérico', async () => {
    const usuario = montar('/ingresar', crearServidorFalso())

    await ingresar(usuario, 'nadie@consultorio-demo.test', CONTRASENA_FICTICIA)

    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJE_GENERICO)
    expect(screen.queryByText('Panel del consultorio')).toBeNull()
  })

  it('US-090 CA-2: contraseña incorrecta muestra el mismo mensaje, conserva el email y vacía la contraseña', async () => {
    const usuario = montar('/ingresar', crearServidorFalso())

    await ingresar(usuario, EMAIL_ACTIVA, 'otra-clave-ficticia')

    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJE_GENERICO)
    expect((screen.getByLabelText('Email') as HTMLInputElement).value).toBe(EMAIL_ACTIVA)
    expect((screen.getByLabelText('Contraseña') as HTMLInputElement).value).toBe('')
  })

  it('US-090 CA-2: los dos rechazos se ven idénticos', async () => {
    const primero = montar('/ingresar', crearServidorFalso())
    await ingresar(primero, 'nadie@consultorio-demo.test', CONTRASENA_FICTICIA)
    const alertaA = await screen.findByRole('alert')
    const vistoA = { texto: alertaA.textContent, rol: alertaA.getAttribute('role') }
    cleanup()

    const segundo = montar('/ingresar', crearServidorFalso())
    await ingresar(segundo, EMAIL_ACTIVA, 'otra-clave-ficticia')
    const alertaB = await screen.findByRole('alert')

    expect({ texto: alertaB.textContent, rol: alertaB.getAttribute('role') }).toEqual(vistoA)
  })

  it('US-090 CA-3: la usuaria inactiva ve el mismo mensaje y no entra', async () => {
    const usuario = montar('/ingresar', crearServidorFalso())

    await ingresar(usuario, EMAIL_INACTIVA, CONTRASENA_FICTICIA)

    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJE_GENERICO)
    expect(screen.queryByText('Panel del consultorio')).toBeNull()
  })

  it('US-090 CA-2: sin conexión muestra el mensaje de conexión y conserva los dos campos', async () => {
    const servidor = crearServidorFalso()
    servidor.caerse()
    const usuario = montar('/ingresar', servidor)

    await ingresar(usuario, EMAIL_ACTIVA, CONTRASENA_FICTICIA)

    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJE_DE_CONEXION)
    expect((screen.getByLabelText('Email') as HTMLInputElement).value).toBe(EMAIL_ACTIVA)
    expect((screen.getByLabelText('Contraseña') as HTMLInputElement).value).toBe(CONTRASENA_FICTICIA)
  })

  it('US-090 CA-1: campos vacíos no hacen ninguna petición', async () => {
    const servidor = crearServidorFalso()
    const usuario = montar('/ingresar', servidor)

    await usuario.click(screen.getByRole('button', { name: 'Ingresar' }))

    expect(servidor.peticiones('/api/auth/login')).toBe(0)
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('US-090 CA-1: el botón queda deshabilitado mientras espera', async () => {
    const servidor = crearServidorFalso()
    const liberar = servidor.retener('/api/auth/login')
    const usuario = montar('/ingresar', servidor)

    await ingresar(usuario, EMAIL_ACTIVA, CONTRASENA_FICTICIA)
    const botonEsperando = await screen.findByRole('button', { name: 'Ingresando…' })
    await usuario.click(botonEsperando)

    expect((botonEsperando as HTMLButtonElement).disabled).toBe(true)
    expect(servidor.peticiones('/api/auth/login')).toBe(1)

    liberar()
    expect(await screen.findByText('Panel del consultorio')).toBeDefined()
  })

  it('US-090 CA-1: la pantalla muestra la marca y solo el formulario de ingreso', () => {
    montar('/ingresar', crearServidorFalso())

    const titulos = screen.getAllByRole('heading')
    expect(titulos).toHaveLength(1)
    expect(titulos[0]?.textContent).toBe('Turnos Odontológicos AR')
    expect(screen.getByRole('heading', { level: 1, name: 'Turnos Odontológicos AR' })).toBeDefined()
    expect(screen.getByLabelText('Email')).toBeDefined()
    expect(screen.getByLabelText('Contraseña')).toBeDefined()
    expect(screen.getAllByRole('button')).toHaveLength(1)
    expect(screen.getByRole('button', { name: 'Ingresar' })).toBeDefined()
    expect(screen.queryAllByRole('link')).toHaveLength(0)
  })

  it('US-090 CA-1: la marca está dentro de la tarjeta de ingreso, junto con el formulario', () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/ingresar']}>
        <App fetch={crearServidorFalso().fetch} />
      </MemoryRouter>,
    )

    const tarjeta = screen.getByRole('region', { name: 'Turnos Odontológicos AR' })
    expect(tarjeta.tagName).toBe('SECTION')
    expect(tarjeta.contains(screen.getByRole('heading', { level: 1 }))).toBe(true)
    expect(tarjeta.contains(container.querySelector('form'))).toBe(true)
  })

  it('US-090 CA-2: el rechazo se muestra en el aviso de error con el mensaje exacto, entre la contraseña y el botón', async () => {
    const usuario = montar('/ingresar', crearServidorFalso())

    await ingresar(usuario, EMAIL_ACTIVA, 'otra-clave-ficticia')

    const avisos = await screen.findAllByRole('alert')
    expect(avisos).toHaveLength(1)
    const aviso = avisos[0] as HTMLElement
    expect(aviso.textContent).toBe(MENSAJE_GENERICO)
    expectEntre(screen.getByLabelText('Contraseña'), aviso, screen.getByRole('button', { name: 'Ingresar' }))
  })

  it('US-090 CA-1: al abrir la pantalla no hay avisos', () => {
    montar('/ingresar', crearServidorFalso())

    expect(screen.queryAllByRole('alert')).toHaveLength(0)
    expect(screen.queryAllByRole('status')).toHaveLength(0)
  })

  it('US-090 CA-3: la usuaria inactiva ve el mismo aviso, en el mismo lugar, que una contraseña incorrecta', async () => {
    const usuario = montar('/ingresar', crearServidorFalso())

    await ingresar(usuario, EMAIL_INACTIVA, CONTRASENA_FICTICIA)

    const avisos = await screen.findAllByRole('alert')
    expect(avisos).toHaveLength(1)
    const aviso = avisos[0] as HTMLElement
    expect(aviso.textContent).toBe(MENSAJE_GENERICO)
    expectEntre(screen.getByLabelText('Contraseña'), aviso, screen.getByRole('button', { name: 'Ingresar' }))
    expect(screen.queryByText('Panel del consultorio')).toBeNull()
  })

  it('US-090 CA-1: mientras espera, el botón conserva el nombre «Ingresando…» con el ícono de espera', async () => {
    const servidor = crearServidorFalso()
    const liberar = servidor.retener('/api/auth/login')
    const usuario = montar('/ingresar', servidor)

    await ingresar(usuario, EMAIL_ACTIVA, CONTRASENA_FICTICIA)
    const boton = (await screen.findByRole('button', { name: 'Ingresando…' })) as HTMLButtonElement

    expect(boton.disabled).toBe(true)
    expect(boton.querySelector('svg')?.getAttribute('aria-hidden')).toBe('true')

    liberar()
    expect(await screen.findByText('Panel del consultorio')).toBeDefined()
  })

  it('US-090 CA-1: sin conexión, el aviso muestra el mensaje de conexión en el lugar del genérico y el botón vuelve a «Ingresar» sin el ícono', async () => {
    const servidor = crearServidorFalso()
    servidor.caerse()
    const usuario = montar('/ingresar', servidor)

    await ingresar(usuario, EMAIL_ACTIVA, CONTRASENA_FICTICIA)

    const avisos = await screen.findAllByRole('alert')
    expect(avisos).toHaveLength(1)
    const aviso = avisos[0] as HTMLElement
    expect(aviso.textContent).toBe(MENSAJE_DE_CONEXION)
    const boton = screen.getByRole('button', { name: 'Ingresar' }) as HTMLButtonElement
    expectEntre(screen.getByLabelText('Contraseña'), aviso, boton)
    expect(boton.disabled).toBe(false)
    expect(boton.querySelector('svg')).toBeNull()
  })
})
