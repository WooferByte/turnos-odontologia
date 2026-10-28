import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { App } from '../../App'
import { CLAVE_DE_SESION } from '../../shared/api/sesion'
import {
  EMAIL_ACTIVA,
  PRESTACIONES_DE_PARTIDA,
  TURNOS_DE_LA_AGENDA,
  crearServidorFalso,
  type OpcionesDelServidorFalso,
  type ServidorFalso,
  type TurnoFalso,
} from '../../test/servidorFalso'

type Usuario = ReturnType<typeof userEvent.setup>

const MENSAJE_DE_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'
const MENSAJE_SIN_TURNOS = 'No hay turnos para este día.'

function LugarActual() {
  const ubicacion = useLocation()
  return <p data-testid="lugar">{ubicacion.pathname}</p>
}

/** El falso con las prestaciones de la demo y, si no se pide otra cosa, los tres turnos del 2 de noviembre. */
function falso(opciones: OpcionesDelServidorFalso = {}): ServidorFalso {
  return crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA, turnos: TURNOS_DE_LA_AGENDA, ...opciones })
}

/** Monta la aplicación con una sesión guardada (como tras recargar). */
function abrirPanel(servidor: ServidorFalso, ruta = '/panel', email = EMAIL_ACTIVA): Usuario {
  sessionStorage.setItem(CLAVE_DE_SESION, JSON.stringify({ refresh: servidor.emitirSesion(email).refresh }))
  render(
    <MemoryRouter initialEntries={[ruta]}>
      <LugarActual />
      <App fetch={servidor.fetch} />
    </MemoryRouter>,
  )
  return userEvent.setup()
}

/** Las filas de datos de la tabla (sin el encabezado), con el texto de cada celda. */
function filasDeLaAgenda(): string[][] {
  return screen
    .getAllByRole('row')
    .slice(1)
    .map((fila) => within(fila).getAllByRole('cell').map((celda) => celda.textContent ?? ''))
}

function colorDeLaMarca(fila: HTMLElement): string {
  const marca = fila.querySelector<HTMLElement>('[data-color]')
  if (marca === null) throw new Error('La fila no tiene marca de color')
  return getComputedStyle(marca).backgroundColor
}

function peticionesDeTurnos(servidor: ServidorFalso): string[] {
  return servidor.rutasPedidas().filter((ruta) => ruta.startsWith('/api/turnos'))
}

beforeEach(() => {
  sessionStorage.clear()
})

afterEach(() => {
  cleanup()
})

describe('PaginaAgenda: el día', () => {
  it('AGE-4a: la odontóloga ve la agenda de hoy', async () => {
    const servidor = falso()
    const usuario = abrirPanel(servidor)

    await usuario.click(await screen.findByRole('link', { name: 'Agenda' }))

    await screen.findByText('lunes 2 de noviembre de 2026')
    expect(filasDeLaAgenda()).toEqual([
      ['09:00 – 09:30', 'Ana Ejemplo', 'Consulta / control', 'Reservado'],
      ['10:00 – 10:45', 'Bruno Ficticio', 'Limpieza', 'Reservado'],
      ['11:00 – 12:00', 'Carla Inventada', 'Obturación', 'Confirmado'],
    ])
    const filas = screen.getAllByRole('row').slice(1)
    expect(filas.map(colorDeLaMarca)).toEqual(['rgb(30, 136, 229)', 'rgb(67, 160, 71)', 'rgb(251, 140, 0)'])
    expect(servidor.peticiones('/api/turnos')).toBe(1)
    expect(peticionesDeTurnos(servidor)).toEqual(['/api/turnos'])
  })

  it('AGE-4b: cambiar de día y volver a hoy', async () => {
    const servidor = falso()
    const usuario = abrirPanel(servidor, '/panel/agenda')
    await screen.findByText('lunes 2 de noviembre de 2026')

    await usuario.click(screen.getByRole('button', { name: 'Día siguiente' }))
    await screen.findByText('martes 3 de noviembre de 2026')
    expect(screen.getByText(MENSAJE_SIN_TURNOS)).toBeDefined()

    await usuario.click(screen.getByRole('button', { name: 'Día anterior' }))
    await screen.findByText('lunes 2 de noviembre de 2026')
    await usuario.click(screen.getByRole('button', { name: 'Día anterior' }))
    await screen.findByText('domingo 1 de noviembre de 2026')

    fireEvent.change(screen.getByLabelText('Fecha de la agenda'), { target: { value: '2026-11-10' } })
    await screen.findByText('martes 10 de noviembre de 2026')

    await usuario.click(screen.getByRole('button', { name: 'Hoy' }))
    await screen.findByText('lunes 2 de noviembre de 2026')
    expect(filasDeLaAgenda()).toHaveLength(3)
    expect(peticionesDeTurnos(servidor)).toEqual([
      '/api/turnos',
      '/api/turnos?fecha=2026-11-03',
      '/api/turnos?fecha=2026-11-02',
      '/api/turnos?fecha=2026-11-01',
      '/api/turnos?fecha=2026-11-10',
    ])
    expect(servidor.peticiones('/api/turnos')).toBe(2)
    expect(servidor.peticiones('/api/turnos?fecha=2026-11-02')).toBe(1)
  })

  it('AGE-4b: el día siguiente cruza fin de mes y de año', async () => {
    const servidor = falso({ hoy: '2026-12-31', turnos: [] })
    const usuario = abrirPanel(servidor, '/panel/agenda')
    await screen.findByText('jueves 31 de diciembre de 2026')

    await usuario.click(screen.getByRole('button', { name: 'Día siguiente' }))

    await screen.findByText('viernes 1 de enero de 2027')
    expect(servidor.peticiones('/api/turnos?fecha=2027-01-01')).toBe(1)
  })

  it('AGE-4b: el día anterior cruza fin de mes', async () => {
    const servidor = falso({ hoy: '2026-03-01', turnos: [] })
    const usuario = abrirPanel(servidor, '/panel/agenda')
    await screen.findByText('domingo 1 de marzo de 2026')

    await usuario.click(screen.getByRole('button', { name: 'Día anterior' }))

    await screen.findByText('sábado 28 de febrero de 2026')
    expect(servidor.peticiones('/api/turnos?fecha=2026-02-28')).toBe(1)
  })

  it('AGE-4c: cada estado se ve con su etiqueta', async () => {
    const estados = [
      ['pendiente_aprobacion', 'Pendiente de aprobación'],
      ['pendiente_sena', 'Pendiente de seña'],
      ['reservado', 'Reservado'],
      ['confirmado', 'Confirmado'],
      ['cancelado_paciente', 'Cancelado por el paciente'],
      ['cancelado_consultorio', 'Cancelado por el consultorio'],
      ['vencido', 'Vencido'],
      ['atendido', 'Atendido'],
      ['ausente', 'Ausente'],
    ] as const
    const turnos: TurnoFalso[] = estados.map(([estado], i) => ({
      id: 100 + i,
      inicio: `2026-11-02T${String(11 + i).padStart(2, '0')}:00:00Z`,
      fin: `2026-11-02T${String(11 + i).padStart(2, '0')}:30:00Z`,
      estado,
      profesional_id: 1,
      sillon_id: 1,
      paciente_id: 1,
      prestacion_id: 1,
    }))
    const servidor = falso({ turnos })
    abrirPanel(servidor, '/panel/agenda')
    await screen.findByText('lunes 2 de noviembre de 2026')

    expect(filasDeLaAgenda().map((celdas) => celdas[3])).toEqual(estados.map(([, etiqueta]) => etiqueta))
  })

  it('AGE-4d: mientras carga se ve «Cargando agenda…» sin filas', async () => {
    const servidor = falso()
    const liberar = servidor.retener('/api/turnos')
    abrirPanel(servidor, '/panel/agenda')

    expect(await screen.findByText('Cargando agenda…')).toBeDefined()
    expect(screen.queryByRole('row')).toBeNull()
    liberar()

    await screen.findByText('lunes 2 de noviembre de 2026')
    expect(screen.queryByText('Cargando agenda…')).toBeNull()
  })

  it('AGE-4d: sin conexión se ve el mensaje con Reintentar, que al responder la API muestra el día', async () => {
    const servidor = falso()
    const liberar = servidor.retener('/api/turnos')
    const usuario = abrirPanel(servidor, '/panel/agenda')
    await screen.findByText('Cargando agenda…')
    servidor.caerse()
    liberar()

    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_DE_CONEXION)
    expect(screen.queryByText('Cargando agenda…')).toBeNull()
    servidor.recuperar()
    await usuario.click(screen.getByRole('button', { name: 'Reintentar' }))

    await screen.findByText('lunes 2 de noviembre de 2026')
    expect(filasDeLaAgenda()).toHaveLength(3)
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('AGE-4d: sin roles se ve el 403 de la lectura, sin tabla ni Reintentar y sin renovar la sesión', async () => {
    const servidor = falso()
    servidor.quitarPermiso(EMAIL_ACTIVA)
    abrirPanel(servidor, '/panel/agenda')

    const aviso = await screen.findByRole('alert')

    expect(aviso.textContent).toContain('Tu usuario no tiene permiso para ver la agenda (RN-AU-05).')
    expect(screen.queryByRole('table')).toBeNull()
    expect(screen.queryByRole('button', { name: 'Reintentar' })).toBeNull()
    // Solo la renovación del arranque: el 403 no la repite.
    await waitFor(() => expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(1))
    expect(screen.getByTestId('lugar').textContent).toBe('/panel/agenda')
  })
})
