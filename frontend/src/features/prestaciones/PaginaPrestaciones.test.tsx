import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
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
const MENSAJE_RN_AG_01 = 'La duración debe ser mayor que 0 y múltiplo de 5 minutos (RN-AG-01).'
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

type Usuario = ReturnType<typeof userEvent.setup>

/** Abre el panel de alta y completa nombre, duración y (si se pide) color; no pulsa «Guardar». */
async function completarAlta(
  usuario: Usuario,
  datos: { nombre: string; duracion: string; color?: string; reservaOnline?: boolean },
) {
  await usuario.click(screen.getByRole('button', { name: 'Nueva prestación' }))
  const nombre = screen.getByLabelText('Nombre')
  await usuario.clear(nombre)
  if (datos.nombre !== '') await usuario.type(nombre, datos.nombre)
  const duracion = screen.getByLabelText('Duración en minutos')
  await usuario.clear(duracion)
  if (datos.duracion !== '') await usuario.type(duracion, datos.duracion)
  if (datos.color !== undefined) fireEvent.input(screen.getByLabelText('Color'), { target: { value: datos.color } })
  if (datos.reservaOnline === true) await usuario.click(screen.getByLabelText('Ofrecer en la reserva online'))
}

describe('PaginaPrestaciones: alta', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-001 CA-1: alta de Blanqueamiento agrega la fila y cierra el panel', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await completarAlta(usuario, { nombre: 'Blanqueamiento', duracion: '60', color: '#3A7BD5' })
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => expect(filasDeDatos()).toHaveLength(6))
    expect(servidor.llamadas('POST', '/api/prestaciones')).toBe(1)
    expect(servidor.cuerpos('POST', '/api/prestaciones')).toEqual([
      { nombre: 'Blanqueamiento', duracion_minutos: 60, color: '#3A7BD5', reservable_online: false },
    ])
    const nueva = within(filaDe('Blanqueamiento'))
    expect(nueva.getByText('60 min')).toBeDefined()
    expect(nueva.getByText('Activa')).toBeDefined()
    expect(screen.queryByRole('complementary')).toBeNull()
  })

  it('US-001 CA-1: reserva online marcada manda true y la fila dice Sí', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await completarAlta(usuario, { nombre: 'Control de ortodoncia', duracion: '30', reservaOnline: true })
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => expect(filasDeDatos()).toHaveLength(6))
    expect(servidor.cuerpos('POST', '/api/prestaciones')[0]?.reservable_online).toBe(true)
    expect(within(filaDe('Control de ortodoncia')).getByText('Sí')).toBeDefined()
  })

  it('US-001 CA-1: nombre o duración vacíos no hacen ninguna petición', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await completarAlta(usuario, { nombre: '', duracion: '30' })
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))
    await usuario.clear(screen.getByLabelText('Duración en minutos'))
    await usuario.type(screen.getByLabelText('Nombre'), 'Blanqueamiento')
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    expect(servidor.llamadas('POST', '/api/prestaciones')).toBe(0)
    expect(screen.getByRole('complementary')).toBeDefined()
    expect(filasDeDatos()).toHaveLength(5)
  })

  it('US-001 CA-1: el botón queda deshabilitado mientras espera', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')
    await completarAlta(usuario, { nombre: 'Blanqueamiento', duracion: '60' })
    const liberar = servidor.retener('/api/prestaciones')

    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))
    const guardando = await screen.findByRole('button', { name: 'Guardando…' })
    await usuario.click(guardando)

    expect((guardando as HTMLButtonElement).disabled).toBe(true)
    liberar()
    await waitFor(() => expect(filasDeDatos()).toHaveLength(6))
    expect(servidor.llamadas('POST', '/api/prestaciones')).toBe(1)
  })

  it('US-001 CA-1: nombre repetido muestra RN-AG-15 debajo del nombre y conserva lo escrito', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await completarAlta(usuario, { nombre: 'limpieza', duracion: '45' })
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    const mensaje = await screen.findByText('Ya existe una prestación con ese nombre (RN-AG-15).')
    const nombre = screen.getByLabelText<HTMLInputElement>('Nombre')
    expect(nombre.getAttribute('aria-describedby')).toBe(mensaje.id)
    expect(nombre.value).toBe('limpieza')
    expect(screen.getByLabelText<HTMLInputElement>('Duración en minutos').value).toBe('45')
    expect(filasDeDatos()).toHaveLength(5)
    expect(servidor.catalogoActual()).toHaveLength(5)
  })

  it('US-001 CA-1: nombre solo de espacios muestra «Ingresá un nombre.»', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await completarAlta(usuario, { nombre: '   ', duracion: '30' })
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    expect(await screen.findByText('Ingresá un nombre.')).toBeDefined()
    expect(servidor.llamadas('POST', '/api/prestaciones')).toBe(1)
    expect(filasDeDatos()).toHaveLength(5)
  })

  it('US-001 CA-1: sin conexión al guardar el alta muestra el aviso del panel, conserva lo escrito y rehabilita Guardar', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')
    await completarAlta(usuario, { nombre: 'Blanqueamiento', duracion: '60' })
    servidor.caerse()

    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJE_DE_CONEXION)
    expect(screen.getByLabelText<HTMLInputElement>('Nombre').value).toBe('Blanqueamiento')
    expect(screen.getByLabelText<HTMLInputElement>('Duración en minutos').value).toBe('60')
    expect((screen.getByRole('button', { name: 'Guardar' }) as HTMLButtonElement).disabled).toBe(false)
    expect(filasDeDatos()).toHaveLength(5)
  })

  it('US-092 CA-1: la sesión termina al guardar un alta, vuelve a /ingresar y no crea nada', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')
    await completarAlta(usuario, { nombre: 'Blanqueamiento', duracion: '60' })
    servidor.vencerAccess()
    servidor.invalidarRefresh()

    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    expect((await screen.findByRole('status')).textContent).toBe(AVISO_SESION_TERMINADA)
    expect(lugar()).toBe('/ingresar')
    expect(servidor.catalogoActual()).toHaveLength(5)
  })
})

describe('PaginaPrestaciones: duración inválida', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-001 CA-2: duración 47 muestra RN-AG-01 debajo del campo y no agrega filas', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await completarAlta(usuario, { nombre: 'Blanqueamiento', duracion: '47' })
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    const mensaje = await screen.findByText(MENSAJE_RN_AG_01)
    const duracion = screen.getByLabelText<HTMLInputElement>('Duración en minutos')
    expect(servidor.cuerpos('POST', '/api/prestaciones')[0]?.duracion_minutos).toBe(47)
    expect(duracion.getAttribute('aria-invalid')).toBe('true')
    expect(duracion.getAttribute('aria-describedby')).toContain(mensaje.id)
    expect(duracion.value).toBe('47')
    expect(filasDeDatos()).toHaveLength(5)
  })

  it('US-001 CA-2: duración 45 se acepta sin mensajes', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await completarAlta(usuario, { nombre: 'Blanqueamiento', duracion: '45' })
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => expect(filasDeDatos()).toHaveLength(6))
    expect(within(filaDe('Blanqueamiento')).getByText('45 min')).toBeDefined()
    expect(screen.queryByText(MENSAJE_RN_AG_01)).toBeNull()
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('US-001 CA-2: duración 0 y -5 llegan a la API y muestran RN-AG-01', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')
    await completarAlta(usuario, { nombre: 'Blanqueamiento', duracion: '0' })

    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))
    await screen.findByText(MENSAJE_RN_AG_01)
    await usuario.clear(screen.getByLabelText('Duración en minutos'))
    await usuario.type(screen.getByLabelText('Duración en minutos'), '-5')
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => expect(servidor.llamadas('POST', '/api/prestaciones')).toBe(2))
    expect(servidor.cuerpos('POST', '/api/prestaciones').map((c) => c.duracion_minutos)).toEqual([0, -5])
    expect(await screen.findByText(MENSAJE_RN_AG_01)).toBeDefined()
    expect(filasDeDatos()).toHaveLength(5)
  })

  it('US-001 CA-2: con duración 47 y nombre repetido se ve solo RN-AG-01', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await completarAlta(usuario, { nombre: 'Limpieza', duracion: '47' })
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    expect(await screen.findByText(MENSAJE_RN_AG_01)).toBeDefined()
    expect(screen.queryByText('Ya existe una prestación con ese nombre (RN-AG-15).')).toBeNull()
  })
})
