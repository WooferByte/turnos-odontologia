import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useEffect } from 'react'
import { MemoryRouter, useLocation, useNavigate } from 'react-router'
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

function RegistroDeUbicaciones({ registro }: { registro: string[] }) {
  const ubicacion = useLocation()
  useEffect(() => {
    registro.push(ubicacion.pathname + ubicacion.search + ubicacion.hash)
  }, [registro, ubicacion.pathname, ubicacion.search, ubicacion.hash])
  return null
}

function ControlesDeNavegacion() {
  const navegar = useNavigate()
  return (
    <div>
      <button type="button" onClick={() => void navegar(-1)}>
        Atrás de prueba
      </button>
      <button type="button" onClick={() => void navegar('/panel')}>
        Ir al panel de prueba
      </button>
    </div>
  )
}

function montarConControles(entradas: string[], indice: number, servidor: ServidorFalso, registro: string[] = []) {
  render(
    <MemoryRouter initialEntries={entradas} initialIndex={indice}>
      <LugarActual />
      <RegistroDeUbicaciones registro={registro} />
      <ControlesDeNavegacion />
      <App fetch={servidor.fetch} />
    </MemoryRouter>,
  )
  return userEvent.setup()
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

  it('US-092 CA-1: con sesión, /ingresar lleva al panel', async () => {
    const servidor = crearServidorFalso()
    guardarRefresh(servidor.emitirSesion().refresh)
    const liberar = servidor.retener('/api/auth/refresh')
    montar('/ingresar', servidor)

    expect(screen.getByText('Cargando…')).toBeDefined()
    expect(screen.queryByRole('button', { name: 'Ingresar' })).toBeNull()
    liberar()

    expect(await screen.findByText('Panel del consultorio')).toBeDefined()
    expect(lugar()).toBe('/panel')
  })

  it('US-092 CA-1: / y una ruta desconocida llevan al panel o al inicio de sesión', async () => {
    for (const ruta of ['/', '/no-existe']) {
      montar(ruta, crearServidorFalso())
      expect(await screen.findByRole('button', { name: 'Ingresar' })).toBeDefined()
      expect(lugar()).toBe('/ingresar')
      cleanup()
    }

    const conSesion = crearServidorFalso()
    guardarRefresh(conSesion.emitirSesion().refresh)
    montar('/no-existe', conSesion)
    expect(await screen.findByText('Panel del consultorio')).toBeDefined()
    expect(lugar()).toBe('/panel')
  })

  it('US-090 CA-1: cerrar sesión borra los tokens y no pide nada a la API', async () => {
    const servidor = crearServidorFalso()
    guardarRefresh(servidor.emitirSesion().refresh)
    const usuario = montar('/panel', servidor)
    await screen.findByText('Panel del consultorio')
    const antes = { refresh: servidor.peticiones('/api/auth/refresh'), login: servidor.peticiones('/api/auth/login') }

    await usuario.click(screen.getByRole('button', { name: 'Cerrar sesión' }))

    expect(await screen.findByRole('button', { name: 'Ingresar' })).toBeDefined()
    expect(lugar()).toBe('/ingresar')
    expect(sessionStorage.getItem(CLAVE_DE_SESION)).toBeNull()
    expect(servidor.peticiones('/api/auth/refresh')).toBe(antes.refresh)
    expect(servidor.peticiones('/api/auth/login')).toBe(antes.login)
  })

  it('US-092 CA-1: después de cerrar sesión, volver a /panel muestra el inicio de sesión', async () => {
    const servidor = crearServidorFalso()
    guardarRefresh(servidor.emitirSesion().refresh)
    const usuario = montarConControles(['/ingresar', '/panel'], 1, servidor)
    await screen.findByText('Panel del consultorio')
    await usuario.click(screen.getByRole('button', { name: 'Cerrar sesión' }))
    await screen.findByRole('button', { name: 'Ingresar' })

    await usuario.click(screen.getByRole('button', { name: 'Atrás de prueba' }))
    expect(screen.queryByText('Panel del consultorio')).toBeNull()
    await usuario.click(screen.getByRole('button', { name: 'Ir al panel de prueba' }))

    expect(await screen.findByRole('button', { name: 'Ingresar' })).toBeDefined()
    expect(lugar()).toBe('/ingresar')
    expect(screen.queryByText('Panel del consultorio')).toBeNull()
  })

  it('US-092 CA-1: con la API caída al recargar se muestra el mensaje de conexión y se conserva el refresh', async () => {
    const servidor = crearServidorFalso()
    const { refresh } = servidor.emitirSesion()
    guardarRefresh(refresh)
    servidor.caerse()
    montar('/panel', servidor)

    expect((await screen.findByRole('alert')).textContent).toBe(
      'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.',
    )
    expect(lugar()).toBe('/ingresar')
    expect(JSON.parse(sessionStorage.getItem(CLAVE_DE_SESION) ?? 'null')).toEqual({ refresh })
  })

  it('US-092 CA-1: ninguna URL visitada contiene un token ni la contraseña', async () => {
    const registro: string[] = []
    const usuario = montarConControles(['/panel/algo'], 0, crearServidorFalso(), registro)

    await usuario.type(await screen.findByLabelText('Email'), EMAIL_ACTIVA)
    await usuario.type(screen.getByLabelText('Contraseña'), CONTRASENA_FICTICIA)
    await usuario.click(screen.getByRole('button', { name: 'Ingresar' }))
    await screen.findByText('Panel del consultorio')
    await usuario.click(screen.getByRole('button', { name: 'Cerrar sesión' }))
    await screen.findByRole('button', { name: 'Ingresar' })

    expect(registro).toContain('/panel/algo')
    expect(registro.length).toBeGreaterThanOrEqual(3)
    for (const url of registro) {
      expect(url).not.toMatch(/acceso-|refresco-|token|\?/)
      expect(url).not.toContain(CONTRASENA_FICTICIA)
    }
  })

  it('US-092 CA-1: el aviso de sesión terminada va antes de los campos y se va al reintentar', async () => {
    const servidor = crearServidorFalso()
    guardarRefresh('refresco-que-el-servidor-no-conoce')
    const usuario = montar('/panel', servidor)

    const aviso = await screen.findByRole('status')
    expect(aviso.textContent).toBe(AVISO_SESION_TERMINADA)
    expect(aviso.compareDocumentPosition(screen.getByLabelText('Email')) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()

    await usuario.type(screen.getByLabelText('Email'), EMAIL_ACTIVA)
    await usuario.type(screen.getByLabelText('Contraseña'), 'otra-clave-ficticia')
    await usuario.click(screen.getByRole('button', { name: 'Ingresar' }))

    expect((await screen.findByRole('alert')).textContent).toBe('El email o la contraseña no son correctos.')
    expect(screen.queryAllByRole('status')).toHaveLength(0)
  })
})
