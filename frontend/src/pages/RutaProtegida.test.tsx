import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { App } from '../App'
import { CLAVE_DE_SESION } from '../shared/api/sesion'
import {
  CONTRASENA_FICTICIA,
  EMAIL_ACTIVA,
  crearServidorFalso,
  type ServidorFalso,
} from '../test/servidorFalso'

const AVISO_SESION_TERMINADA = 'Tu sesión terminó. Iniciá sesión de nuevo.'

function LugarActual() {
  const ubicacion = useLocation()
  return <p data-testid="lugar">{ubicacion.pathname}</p>
}

function montar(ruta: string, servidor: ServidorFalso) {
  render(
    <MemoryRouter initialEntries={[ruta]}>
      <LugarActual />
      <App fetch={servidor.fetch} />
    </MemoryRouter>,
  )
  return userEvent.setup()
}

function lugar(): string | null {
  return screen.getByTestId('lugar').textContent
}

function guardarRefresh(refresh: string): void {
  sessionStorage.setItem(CLAVE_DE_SESION, JSON.stringify({ refresh }))
}

describe('RutaProtegida y arranque', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-092 CA-1: el panel sin sesión lleva a /ingresar sin pedir nada a la API', async () => {
    const servidor = crearServidorFalso()
    montar('/panel', servidor)

    expect(await screen.findByRole('button', { name: 'Ingresar' })).toBeDefined()
    expect(lugar()).toBe('/ingresar')
    expect(screen.queryByText('Panel del consultorio')).toBeNull()
    expect(servidor.peticiones('/api/auth/refresh')).toBe(0)
    expect(servidor.peticiones('/api/auth/login')).toBe(0)
  })

  it('US-090 CA-1: tras iniciar sesión vuelve a la ruta del panel pedida', async () => {
    const usuario = montar('/panel/algo', crearServidorFalso())

    await usuario.type(await screen.findByLabelText('Email'), EMAIL_ACTIVA)
    await usuario.type(screen.getByLabelText('Contraseña'), CONTRASENA_FICTICIA)
    await usuario.click(screen.getByRole('button', { name: 'Ingresar' }))

    expect(await screen.findByText('Panel del consultorio')).toBeDefined()
    expect(lugar()).toBe('/panel/algo')
  })

  it('US-092 CA-1: al recargar con un refresh guardado renueva y muestra el panel', async () => {
    const servidor = crearServidorFalso()
    guardarRefresh(servidor.emitirSesion().refresh)
    const liberar = servidor.retener('/api/auth/refresh')
    montar('/panel', servidor)

    expect(screen.getByText('Cargando…')).toBeDefined()
    expect(screen.queryByText('Panel del consultorio')).toBeNull()
    liberar()

    expect(await screen.findByText('Panel del consultorio')).toBeDefined()
    expect(screen.queryByText('Cargando…')).toBeNull()
    expect(servidor.peticiones('/api/auth/refresh')).toBe(1)
  })

  it('US-092 CA-1: al recargar con un refresh rechazado muestra el aviso de sesión terminada', async () => {
    const servidor = crearServidorFalso()
    guardarRefresh('refresco-que-el-servidor-no-conoce')
    montar('/panel', servidor)

    expect((await screen.findByRole('status')).textContent).toBe(AVISO_SESION_TERMINADA)
    expect(lugar()).toBe('/ingresar')
    expect(screen.queryByText('Panel del consultorio')).toBeNull()
    expect(sessionStorage.getItem(CLAVE_DE_SESION)).toBeNull()
  })
})
