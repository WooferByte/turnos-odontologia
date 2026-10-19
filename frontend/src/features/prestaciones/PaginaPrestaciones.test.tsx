import { cleanup, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { App } from '../../App'
import { CLAVE_DE_SESION } from '../../shared/api/sesion'
import {
  EMAIL_ACTIVA,
  EMAIL_RECEPCIONISTA,
  PRESTACIONES_DE_PARTIDA,
  crearServidorFalso,
  type ServidorFalso,
} from '../../test/servidorFalso'

const AVISO_SESION_TERMINADA = 'Tu sesión terminó. Iniciá sesión de nuevo.'
const MENSAJE_DE_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'

function LugarActual() {
  const ubicacion = useLocation()
  return <p data-testid="lugar">{ubicacion.pathname}</p>
}

function lugar(): string | null {
  return screen.getByTestId('lugar').textContent
}

/** Monta la aplicación con una sesión guardada (como tras recargar) y espera a que cargue el panel. */
async function abrirPanel(servidor: ServidorFalso, ruta = '/panel', email = EMAIL_ACTIVA) {
  sessionStorage.setItem(CLAVE_DE_SESION, JSON.stringify({ refresh: servidor.emitirSesion(email).refresh }))
  render(
    <MemoryRouter initialEntries={[ruta]}>
      <LugarActual />
      <App fetch={servidor.fetch} />
    </MemoryRouter>,
  )
  return userEvent.setup()
}

function filasDeDatos(): HTMLTableRowElement[] {
  return within(screen.getByRole('table')).getAllByRole<HTMLTableRowElement>('row').slice(1)
}

function filaDe(nombre: string): HTMLElement {
  const fila = screen.getByRole('cell', { name: nombre }).closest('tr')
  if (fila === null) throw new Error(`No hay fila para ${nombre}`)
  return fila
}

describe('PaginaPrestaciones: listado y sesión', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-001 CA-1: el enlace Prestaciones lleva a la tabla con activas e inactivas', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor)
    await screen.findByText('Panel del consultorio')

    await usuario.click(screen.getByRole('link', { name: 'Prestaciones' }))

    await screen.findByRole('table')
    expect(lugar()).toBe('/panel/prestaciones')
    expect(servidor.llamadas('GET', '/api/prestaciones')).toBe(1)
    expect(filasDeDatos().map((fila) => fila.cells[1]?.textContent)).toEqual([
      'Consulta / control',
      'Limpieza',
      'Obturación',
      'Extracción',
      'Urgencia',
    ])
    const limpieza = within(filaDe('Limpieza'))
    expect(limpieza.getByText('45 min')).toBeDefined()
    expect(limpieza.getByRole('img', { name: 'Color #43A047' })).toBeDefined()
    expect(limpieza.getByText('No')).toBeDefined()
    expect(limpieza.getByText('Activa')).toBeDefined()
    const urgencia = filaDe('Urgencia')
    expect(urgencia.className).toContain('inactiva')
    expect(within(urgencia).getByText('Inactiva')).toBeDefined()
    expect(within(urgencia).getByRole('button', { name: 'Reactivar Urgencia' })).toBeDefined()
  })

  it('US-092 CA-1: una sesión irrenovable al abrir la pantalla vuelve a /ingresar con el aviso', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor)
    await screen.findByText('Panel del consultorio')
    servidor.vencerAccess()
    servidor.invalidarRefresh()

    await usuario.click(screen.getByRole('link', { name: 'Prestaciones' }))

    expect((await screen.findByRole('status')).textContent).toBe(AVISO_SESION_TERMINADA)
    expect(lugar()).toBe('/ingresar')
    expect(screen.queryByText(MENSAJE_DE_CONEXION)).toBeNull()
    expect(screen.queryByRole('table')).toBeNull()
  })

  it('US-001 CA-1: sin prestaciones muestra «Todavía no hay prestaciones.» y Nueva prestación', async () => {
    await abrirPanel(crearServidorFalso(), '/panel/prestaciones')

    expect(await screen.findByText('Todavía no hay prestaciones.')).toBeDefined()
    expect(screen.getByRole('button', { name: 'Nueva prestación' })).toBeDefined()
    expect(screen.queryByRole('table')).toBeNull()
  })

  it('US-001 CA-1: mientras carga muestra «Cargando prestaciones…» y después la tabla', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const liberar = servidor.retener('/api/prestaciones')
    await abrirPanel(servidor, '/panel/prestaciones')

    expect(await screen.findByText('Cargando prestaciones…')).toBeDefined()
    expect(screen.queryByRole('table')).toBeNull()
    expect(screen.queryAllByRole('row')).toHaveLength(0)
    liberar()

    await screen.findByRole('table')
    expect(screen.queryByText('Cargando prestaciones…')).toBeNull()
    expect(filasDeDatos()).toHaveLength(5)
  })

  it('US-001 CA-1: sin conexión muestra el mensaje y Reintentar recupera la tabla', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor)
    await screen.findByText('Panel del consultorio')
    servidor.caerse()

    await usuario.click(screen.getByRole('link', { name: 'Prestaciones' }))

    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_DE_CONEXION)
    expect(screen.queryByRole('table')).toBeNull()
    servidor.recuperar()
    await usuario.click(screen.getByRole('button', { name: 'Reintentar' }))

    await screen.findByRole('table')
    expect(filasDeDatos()).toHaveLength(5)
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('US-001 CA-1: la recepcionista ve las cinco prestaciones', async () => {
    await abrirPanel(
      crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA }),
      '/panel/prestaciones',
      EMAIL_RECEPCIONISTA,
    )

    await screen.findByRole('table')
    expect(filasDeDatos()).toHaveLength(5)
  })

  it('US-092 CA-1: un access vencido se renueva y la tabla carga', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor)
    await screen.findByText('Panel del consultorio')
    const refrescosAntes = servidor.llamadas('POST', '/api/auth/refresh')
    servidor.vencerAccess()

    await usuario.click(screen.getByRole('link', { name: 'Prestaciones' }))

    await screen.findByRole('table')
    expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(refrescosAntes + 1)
    expect(servidor.llamadas('GET', '/api/prestaciones')).toBe(2)
    expect(lugar()).toBe('/panel/prestaciones')
    expect(filasDeDatos()).toHaveLength(5)
  })
})
