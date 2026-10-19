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
const MENSAJE_SIN_PERMISO = 'Tu usuario no tiene permiso para modificar prestaciones (RN-AU-05).'
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

describe('PaginaPrestaciones: edición, desactivación y aviso de CA-3', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-001 CA-1: editar solo el color manda solo color y actualiza la muestra', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await usuario.click(screen.getByRole('button', { name: 'Editar Limpieza' }))
    fireEvent.input(screen.getByLabelText('Color'), { target: { value: '#F9A825' } })
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => expect(screen.queryByRole('complementary')).toBeNull())
    expect(servidor.cuerpos('PATCH', '/api/prestaciones/2')).toEqual([{ color: '#F9A825' }])
    const limpieza = within(filaDe('Limpieza'))
    expect(limpieza.getByRole('img', { name: 'Color #F9A825' })).toBeDefined()
    expect(limpieza.getByText('45 min')).toBeDefined()
    expect(limpieza.getByText('Activa')).toBeDefined()
  })

  it('US-001 CA-1: desactivar Extracción manda {"activa": false} y la fila queda atenuada con Inactiva y Reactivar', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await usuario.click(screen.getByRole('button', { name: 'Desactivar Extracción' }))

    const fila = await waitFor(() => {
      const actual = filaDe('Extracción')
      expect(within(actual).getByText('Inactiva')).toBeDefined()
      return actual
    })
    expect(servidor.cuerpos('PATCH', '/api/prestaciones/4')).toEqual([{ activa: false }])
    expect(fila.className).toContain('inactiva')
    expect(within(fila).getByRole('button', { name: 'Reactivar Extracción' })).toBeDefined()
    expect(filasDeDatos()).toHaveLength(5)
  })

  it('US-001 CA-1: guardar sin cambios cierra el panel sin ningún PATCH', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await usuario.click(screen.getByRole('button', { name: 'Editar Limpieza' }))
    expect(screen.getByLabelText<HTMLInputElement>('Nombre').value).toBe('Limpieza')
    expect(screen.getByLabelText<HTMLInputElement>('Duración en minutos').value).toBe('45')
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    expect(screen.queryByRole('complementary')).toBeNull()
    expect(servidor.llamadas('PATCH', '/api/prestaciones/2')).toBe(0)
    expect(within(filaDe('Limpieza')).getByText('45 min')).toBeDefined()
  })

  it('US-001 CA-3: cambiar la duración muestra el aviso, manda solo duracion_minutos y no pide rutas de turnos', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await usuario.click(screen.getByRole('button', { name: 'Editar Consulta / control' }))
    expect(screen.getByText('Cambiar la duración no modifica los turnos ya creados.')).toBeDefined()
    const duracion = screen.getByLabelText('Duración en minutos')
    await usuario.clear(duracion)
    await usuario.type(duracion, '60')
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => expect(within(filaDe('Consulta / control')).getByText('60 min')).toBeDefined())
    expect(servidor.cuerpos('PATCH', '/api/prestaciones/1')).toEqual([{ duracion_minutos: 60 }])
    expect(servidor.rutasPedidas().filter((ruta) => ruta.includes('turno'))).toEqual([])
  })

  it('US-001 CA-2: la edición con 52 muestra RN-AG-01 y la fila sigue en 45; con 50 se guarda y el mensaje desaparece', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await usuario.click(screen.getByRole('button', { name: 'Editar Limpieza' }))
    const duracion = screen.getByLabelText('Duración en minutos')
    await usuario.clear(duracion)
    await usuario.type(duracion, '52')
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    expect(await screen.findByText(MENSAJE_RN_AG_01)).toBeDefined()
    expect(within(filaDe('Limpieza')).getByText('45 min')).toBeDefined()
    await usuario.clear(duracion)
    await usuario.type(duracion, '50')
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => expect(within(filaDe('Limpieza')).getByText('50 min')).toBeDefined())
    expect(screen.queryByText(MENSAJE_RN_AG_01)).toBeNull()
    expect(servidor.cuerpos('PATCH', '/api/prestaciones/2')).toEqual([{ duracion_minutos: 52 }, { duracion_minutos: 50 }])
  })

  it('US-001 CA-1: reactivar Urgencia manda {"activa": true} y ninguna fila ofrece borrar', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await usuario.click(screen.getByRole('button', { name: 'Reactivar Urgencia' }))

    await waitFor(() => expect(within(filaDe('Urgencia')).getByText('Activa')).toBeDefined())
    expect(servidor.cuerpos('PATCH', '/api/prestaciones/5')).toEqual([{ activa: true }])
    expect(filaDe('Urgencia').className).not.toContain('inactiva')
    expect(within(filaDe('Urgencia')).getByRole('button', { name: 'Desactivar Urgencia' })).toBeDefined()
    expect(screen.queryByRole('button', { name: /borrar|eliminar/i })).toBeNull()
  })

  it('US-001 CA-1: cancelar la edición no pide nada y la fila no cambia', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await usuario.click(screen.getByRole('button', { name: 'Editar Limpieza' }))
    const nombre = screen.getByLabelText('Nombre')
    await usuario.clear(nombre)
    await usuario.type(nombre, 'Limpieza profunda')
    await usuario.click(screen.getByRole('button', { name: 'Cancelar' }))

    expect(screen.queryByRole('complementary')).toBeNull()
    expect(servidor.llamadas('PATCH', '/api/prestaciones/2')).toBe(0)
    expect(filaDe('Limpieza')).toBeDefined()
    expect(screen.queryByRole('cell', { name: 'Limpieza profunda' })).toBeNull()
  })

  it('US-001 CA-1: renombrar Extracción a LIMPIEZA muestra RN-AG-15 y la fila sigue igual', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await usuario.click(screen.getByRole('button', { name: 'Editar Extracción' }))
    const nombre = screen.getByLabelText('Nombre')
    await usuario.clear(nombre)
    await usuario.type(nombre, 'LIMPIEZA')
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    expect(await screen.findByText('Ya existe una prestación con ese nombre (RN-AG-15).')).toBeDefined()
    expect(filaDe('Extracción')).toBeDefined()
    expect(screen.queryByRole('cell', { name: 'LIMPIEZA' })).toBeNull()
    expect(screen.getByRole('complementary')).toBeDefined()
  })

  it('US-001 CA-1: Urgencia que ya no existe muestra RN-GL-04, cierra el panel y la lista recargada tiene cuatro filas', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')
    await usuario.click(screen.getByRole('button', { name: 'Editar Urgencia' }))
    const duracion = screen.getByLabelText('Duración en minutos')
    await usuario.clear(duracion)
    await usuario.type(duracion, '40')
    servidor.quitarPrestacion(5)

    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    expect(await screen.findByText('La prestación ya no existe (RN-GL-04).')).toBeDefined()
    await waitFor(() => expect(filasDeDatos()).toHaveLength(4))
    expect(screen.queryByRole('complementary')).toBeNull()
    expect(screen.queryByRole('cell', { name: 'Urgencia' })).toBeNull()
    expect(servidor.llamadas('PATCH', '/api/prestaciones/5')).toBe(1)
    expect(servidor.llamadas('GET', '/api/prestaciones')).toBe(2)
  })

  it('US-001 CA-1: sin conexión al desactivar muestra el aviso de la tabla y la fila sigue Activa', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')
    servidor.caerse()

    await usuario.click(screen.getByRole('button', { name: 'Desactivar Extracción' }))

    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJE_DE_CONEXION)
    const fila = filaDe('Extracción')
    expect(within(fila).getByText('Activa')).toBeDefined()
    expect(fila.className).not.toContain('inactiva')
    expect((within(fila).getByRole('button', { name: 'Desactivar Extracción' }) as HTMLButtonElement).disabled).toBe(false)
    expect((within(fila).getByRole('button', { name: 'Editar Extracción' }) as HTMLButtonElement).disabled).toBe(false)
  })

  it('US-001 CA-3: el alta no muestra el aviso sobre los turnos', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await usuario.click(screen.getByRole('button', { name: 'Nueva prestación' }))

    expect(screen.getByRole('heading', { name: 'Nueva prestación' })).toBeDefined()
    expect(screen.queryByText('Cambiar la duración no modifica los turnos ya creados.')).toBeNull()
  })

  it('US-001 CA-1: guardar sin cambios una prestación con color en minúsculas no pide nada', async () => {
    const servidor = crearServidorFalso({
      prestaciones: [{ id: 1, nombre: 'Limpieza', duracion_minutos: 45, color: '#43a047', reservable_online: false, activa: true }],
    })
    const usuario = await abrirPanel(servidor, '/panel/prestaciones')
    await screen.findByRole('table')

    await usuario.click(screen.getByRole('button', { name: 'Editar Limpieza' }))
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    expect(screen.queryByRole('complementary')).toBeNull()
    expect(servidor.llamadas('PATCH', '/api/prestaciones/1')).toBe(0)
  })
})

describe('PaginaPrestaciones: la recepcionista lee y la API rechaza con RN-AU-05', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  async function abrirComoRecepcionista(servidor: ServidorFalso) {
    const usuario = await abrirPanel(servidor, '/panel/prestaciones', EMAIL_RECEPCIONISTA)
    await screen.findByRole('table')
    return usuario
  }

  it('US-001 CA-1: la recepcionista que crea ve RN-AU-05 en el aviso del panel, conserva lo escrito, la tabla no cambia y no hay refresh', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirComoRecepcionista(servidor)
    const refrescosAntes = servidor.llamadas('POST', '/api/auth/refresh')

    await completarAlta(usuario, { nombre: 'Blanqueamiento', duracion: '60' })
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    const aviso = await within(screen.getByRole('complementary')).findByRole('alert')
    expect(aviso.textContent).toBe(MENSAJE_SIN_PERMISO)
    expect(screen.getByLabelText<HTMLInputElement>('Nombre').value).toBe('Blanqueamiento')
    expect(screen.getByLabelText<HTMLInputElement>('Duración en minutos').value).toBe('60')
    expect(filasDeDatos()).toHaveLength(5)
    expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(refrescosAntes)
    expect(lugar()).toBe('/panel/prestaciones')
  })

  it('US-001 CA-1: la recepcionista que desactiva o reactiva ve RN-AU-05 en el aviso de la tabla y las filas no cambian', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirComoRecepcionista(servidor)

    await usuario.click(screen.getByRole('button', { name: 'Desactivar Limpieza' }))
    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJE_SIN_PERMISO)
    await usuario.click(screen.getByRole('button', { name: 'Reactivar Urgencia' }))

    await waitFor(() => expect(servidor.llamadas('PATCH', '/api/prestaciones/5')).toBe(1))
    expect(servidor.llamadas('PATCH', '/api/prestaciones/2')).toBe(1)
    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJE_SIN_PERMISO)
    expect(within(filaDe('Limpieza')).getByText('Activa')).toBeDefined()
    expect(within(filaDe('Urgencia')).getByText('Inactiva')).toBeDefined()
  })

  it('US-001 CA-1: sin permiso y con duración 47 se ve RN-AU-05 y no RN-AG-01', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirComoRecepcionista(servidor)

    await completarAlta(usuario, { nombre: 'Blanqueamiento', duracion: '47' })
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    expect(await screen.findByText(MENSAJE_SIN_PERMISO)).toBeDefined()
    expect(screen.queryByText(MENSAJE_RN_AG_01)).toBeNull()
    expect(screen.getByLabelText('Duración en minutos').getAttribute('aria-invalid')).toBeNull()
  })

  it('US-001 CA-1: la recepcionista que edita ve RN-AU-05, el panel sigue con 50 y la fila sigue en 45 min', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirComoRecepcionista(servidor)

    await usuario.click(screen.getByRole('button', { name: 'Editar Limpieza' }))
    const duracion = screen.getByLabelText<HTMLInputElement>('Duración en minutos')
    await usuario.clear(duracion)
    await usuario.type(duracion, '50')
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    const aviso = await within(screen.getByRole('complementary')).findByRole('alert')
    expect(aviso.textContent).toBe(MENSAJE_SIN_PERMISO)
    expect(duracion.value).toBe('50')
    expect(within(filaDe('Limpieza')).getByText('45 min')).toBeDefined()
    expect(servidor.llamadas('PATCH', '/api/prestaciones/2')).toBe(1)
  })
})
