import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { App } from '../../App'
import { CLAVE_DE_SESION } from '../../shared/api/sesion'
import {
  EMAIL_ACTIVA,
  EMAIL_DUENO,
  EMAIL_RECEPCIONISTA,
  PRESTACIONES_DE_PARTIDA,
  TURNOS_DE_LA_AGENDA,
  USUARIOS_DE_PARTIDA,
  USUARIO_DUENO,
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

interface Datos {
  paciente?: string
  prestacion?: string
  fecha?: string
  hora?: string
}

async function abrirAgenda(servidor: ServidorFalso, email = EMAIL_ACTIVA): Promise<Usuario> {
  const usuario = abrirPanel(servidor, '/panel/agenda', email)
  await screen.findByText('lunes 2 de noviembre de 2026')
  return usuario
}

async function abrirNuevoTurno(usuario: Usuario): Promise<HTMLElement> {
  await usuario.click(screen.getByRole('button', { name: 'Nuevo turno' }))
  return screen.findByRole('complementary', { name: 'Nuevo turno' })
}

/** Completa lo que se pida del formulario; las opciones de prestación llegan al abrir el panel. */
async function completarTurno(usuario: Usuario, datos: Datos): Promise<void> {
  if (datos.paciente !== undefined) {
    await usuario.type(screen.getByLabelText('N.º de paciente'), datos.paciente)
  }
  if (datos.prestacion !== undefined) {
    await screen.findByRole('option', { name: datos.prestacion })
    await usuario.selectOptions(screen.getByLabelText('Prestación'), datos.prestacion)
  }
  if (datos.fecha !== undefined) fireEvent.change(screen.getByLabelText('Fecha'), { target: { value: datos.fecha } })
  if (datos.hora !== undefined) fireEvent.change(screen.getByLabelText('Hora'), { target: { value: datos.hora } })
}

function botonCrear(): HTMLButtonElement {
  return screen.getByRole('button', { name: 'Crear turno' })
}

describe('PaginaAgenda: nuevo turno', () => {
  it('AGE-5a: la recepcionista da un turno y lo ve en la agenda', async () => {
    const servidor = falso({ turnos: [TURNOS_DE_LA_AGENDA[0] as TurnoFalso] })
    const usuario = await abrirAgenda(servidor, EMAIL_RECEPCIONISTA)
    await abrirNuevoTurno(usuario)

    await completarTurno(usuario, { paciente: '2', prestacion: 'Limpieza · 45 min', hora: '10:00' })

    expect((screen.getByLabelText('Fecha') as HTMLInputElement).value).toBe('2026-11-02')
    expect(screen.getByText('Termina a las 10:45.')).toBeDefined()
    expect(screen.queryByRole('option', { name: /Urgencia/ })).toBeNull()
    await usuario.click(botonCrear())

    expect(await screen.findByText('Turno creado.')).toBeDefined()
    expect(servidor.cuerpos('POST', '/api/turnos')).toEqual([
      { paciente_id: 2, prestacion_id: 2, inicio: '2026-11-02T13:00:00Z' },
    ])
    expect(servidor.llamadas('POST', '/api/turnos')).toBe(1)
    expect(screen.queryByRole('complementary', { name: 'Nuevo turno' })).toBeNull()
    await waitFor(() => expect(servidor.peticiones('/api/turnos?fecha=2026-11-02')).toBe(1))
    await waitFor(() =>
      expect(filasDeLaAgenda()).toEqual([
        ['09:00 – 09:30', 'Ana Ejemplo', 'Consulta / control', 'Reservado'],
        ['10:00 – 10:45', 'Bruno Ficticio', 'Limpieza', 'Reservado'],
      ]),
    )
  })
})

describe('PaginaAgenda: nuevo turno, bordes', () => {
  it('AGE-5b: un campo vacío no manda nada', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirNuevoTurno(usuario)

    await usuario.click(botonCrear())

    expect((await screen.findByRole('alert')).textContent).toContain('Completá paciente, prestación, fecha y hora.')
    expect(servidor.llamadas('POST', '/api/turnos')).toBe(0)
  })

  it('AGE-5b: Cancelar no manda nada', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirNuevoTurno(usuario)
    await completarTurno(usuario, { paciente: '2', prestacion: 'Limpieza · 45 min', hora: '15:00' })

    await usuario.click(screen.getByRole('button', { name: 'Cancelar' }))

    expect(screen.queryByRole('complementary', { name: 'Nuevo turno' })).toBeNull()
    expect(servidor.llamadas('POST', '/api/turnos')).toBe(0)
  })

  it('AGE-5b: el doble clic manda un solo POST', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirNuevoTurno(usuario)
    await completarTurno(usuario, { paciente: '2', prestacion: 'Limpieza · 45 min', hora: '15:00' })
    const liberar = servidor.retener('/api/turnos')

    await usuario.click(botonCrear())
    await usuario.click(botonCrear())

    expect(botonCrear().disabled).toBe(true)
    liberar()
    expect(await screen.findByText('Turno creado.')).toBeDefined()
    expect(servidor.llamadas('POST', '/api/turnos')).toBe(1)
  })

  it('AGE-5h: un turno en otro día que cruza la medianoche UTC', async () => {
    const servidor = falso({ turnos: [] })
    const usuario = await abrirAgenda(servidor)
    await abrirNuevoTurno(usuario)

    await completarTurno(usuario, { paciente: '2', prestacion: 'Limpieza · 45 min', fecha: '2026-11-03', hora: '22:00' })

    expect(screen.getByText('Termina a las 22:45.')).toBeDefined()
    await usuario.click(botonCrear())
    expect(await screen.findByText('Turno creado.')).toBeDefined()
    expect(servidor.cuerpos('POST', '/api/turnos')).toEqual([
      { paciente_id: 2, prestacion_id: 2, inicio: '2026-11-04T01:00:00Z' },
    ])
    await screen.findByText('martes 3 de noviembre de 2026')
    expect(servidor.peticiones('/api/turnos?fecha=2026-11-03')).toBe(1)
    expect(servidor.peticiones('/api/turnos?fecha=2026-11-04')).toBe(0)
    expect(filasDeLaAgenda()).toEqual([['22:00 – 22:45', 'Bruno Ficticio', 'Limpieza', 'Reservado']])
  })
})

/** Lo cargado en el panel después de un rechazo: sigue abierto, sin «Turno creado.». */
function comprobarQueSeConservaLoCargado(servidor: ServidorFalso, paciente: string, hora: string): void {
  expect(screen.getByRole('complementary', { name: 'Nuevo turno' })).toBeDefined()
  expect((screen.getByLabelText('N.º de paciente') as HTMLInputElement).value).toBe(paciente)
  expect((screen.getByLabelText('Hora') as HTMLInputElement).value).toBe(hora)
  expect(screen.queryByText('Turno creado.')).toBeNull()
  expect(servidor.llamadas('POST', '/api/turnos')).toBe(1)
}

describe('PaginaAgenda: los rechazos al crear', () => {
  it('AGE-5c: E4 muestra los dos códigos', async () => {
    const servidor = falso({ turnos: [TURNOS_DE_LA_AGENDA[0] as TurnoFalso] })
    const usuario = await abrirAgenda(servidor, EMAIL_RECEPCIONISTA)
    await abrirNuevoTurno(usuario)
    await completarTurno(usuario, { paciente: '2', prestacion: 'Consulta / control · 30 min', fecha: '2026-11-02', hora: '09:00' })

    await usuario.click(botonCrear())

    expect((await screen.findByRole('alert')).textContent).toContain(
      'El profesional y el sillón ya tienen un turno activo en ese horario (RN-AG-05, RN-AG-08).',
    )
    expect(servidor.cuerpos('POST', '/api/turnos')).toEqual([
      { paciente_id: 2, prestacion_id: 1, inicio: '2026-11-02T12:00:00Z' },
    ])
    comprobarQueSeConservaLoCargado(servidor, '2', '09:00')
    expect(filasDeLaAgenda()).toHaveLength(1)
  })

  it('AGE-5d: E12 muestra RN-GL-04 con las referencias', async () => {
    const servidor = falso()
    servidor.desactivarTrasListar(2)
    const usuario = await abrirAgenda(servidor)
    await abrirNuevoTurno(usuario)
    await completarTurno(usuario, { paciente: '99', prestacion: 'Limpieza · 45 min', hora: '10:00' })

    await usuario.click(botonCrear())

    expect((await screen.findByRole('alert')).textContent).toContain(
      'Hay datos que no existen o no están activos: paciente 99 (no existe), prestación 2 (inactiva) (RN-GL-04).',
    )
    await waitFor(() => expect(servidor.llamadas('GET', '/api/prestaciones')).toBe(2))
    await waitFor(() => expect(screen.queryByRole('option', { name: 'Limpieza · 45 min' })).toBeNull())
    comprobarQueSeConservaLoCargado(servidor, '99', '10:00')
  })

  it.each([
    [409, ['RN-AG-05'], 'El profesional ya tiene un turno activo en ese horario (RN-AG-05).'],
    [409, ['RN-AG-08'], 'El sillón ya tiene un turno activo en ese horario (RN-AG-08).'],
    [422, ['RN-AG-04'], 'El turno no cae dentro del horario de atención del profesional (RN-AG-04).'],
    [422, ['RN-AG-04b'], 'Ese horario está bloqueado (RN-AG-04b).'],
    [422, ['RN-AG-10d'], 'El turno no puede pasar de la medianoche del consultorio (RN-AG-10d).'],
    [422, ['RN-GL-01'], 'La fecha y hora no es válida (RN-GL-01).'],
    [422, [], 'Revisá los datos del turno.'],
  ])('AGE-5e: el %i con %j se ve como «%s»', async (estado, codigos, texto) => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirNuevoTurno(usuario)
    await completarTurno(usuario, { paciente: '2', prestacion: 'Limpieza · 45 min', hora: '15:00' })
    servidor.responderAlCrear(estado, codigos)

    await usuario.click(botonCrear())

    expect((await screen.findByRole('alert')).textContent).toContain(texto)
    comprobarQueSeConservaLoCargado(servidor, '2', '15:00')
  })

  it('AGE-5f: el dueño no puede crear turnos', async () => {
    const servidor = falso({ usuarios: [...USUARIOS_DE_PARTIDA, USUARIO_DUENO] })
    const usuario = await abrirAgenda(servidor, EMAIL_DUENO)
    await abrirNuevoTurno(usuario)
    await completarTurno(usuario, { paciente: '2', prestacion: 'Limpieza · 45 min', hora: '15:00' })
    const refrescosAntes = servidor.llamadas('POST', '/api/auth/refresh')

    await usuario.click(botonCrear())

    expect((await screen.findByRole('alert')).textContent).toContain(
      'Tu usuario no tiene permiso para crear turnos (RN-AU-05).',
    )
    expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(refrescosAntes)
    expect(screen.getByTestId('lugar').textContent).toBe('/panel/agenda')
    expect(servidor.turnosActuales()).toHaveLength(3)
    comprobarQueSeConservaLoCargado(servidor, '2', '15:00')
  })

  it('AGE-5g: sin conexión al crear se conserva lo cargado', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirNuevoTurno(usuario)
    await completarTurno(usuario, { paciente: '2', prestacion: 'Limpieza · 45 min', hora: '15:00' })
    servidor.caerse()

    await usuario.click(botonCrear())

    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_DE_CONEXION)
    expect(screen.queryByRole('button', { name: 'Reintentar' })).toBeNull()
    expect(botonCrear().disabled).toBe(false)
    expect(screen.queryByText('Turno creado.')).toBeNull()
    expect((screen.getByLabelText('N.º de paciente') as HTMLInputElement).value).toBe('2')
    expect((screen.getByLabelText('Hora') as HTMLInputElement).value).toBe('15:00')
  })
})

const AVISO_SESION_TERMINADA = 'Tu sesión terminó. Iniciá sesión de nuevo.'

describe('PaginaAgenda: la sesión', () => {
  it('AGE-6a: con el refresh vigente, la carga del día se renueva sin aviso', async () => {
    const servidor = falso()
    const usuario = abrirPanel(servidor)
    const enlace = await screen.findByRole('link', { name: 'Agenda' })
    const refrescosAntes = servidor.llamadas('POST', '/api/auth/refresh')
    servidor.vencerAccess()

    await usuario.click(enlace)

    await screen.findByText('lunes 2 de noviembre de 2026')
    expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(refrescosAntes + 1)
    expect(screen.queryByRole('alert')).toBeNull()
    expect(filasDeLaAgenda()).toHaveLength(3)
  })

  it('AGE-6a: una sesión irrenovable al cargar el día vuelve al inicio de sesión', async () => {
    const servidor = falso()
    const usuario = abrirPanel(servidor)
    const enlace = await screen.findByRole('link', { name: 'Agenda' })
    servidor.vencerAccess()
    servidor.invalidarRefresh()

    await usuario.click(enlace)

    expect((await screen.findByRole('status')).textContent).toBe(AVISO_SESION_TERMINADA)
    expect(screen.getByTestId('lugar').textContent).toBe('/ingresar')
    expect(screen.queryByText(MENSAJE_DE_CONEXION)).toBeNull()
  })

  it('AGE-6a: una sesión irrenovable al crear un turno vuelve al inicio de sesión', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirNuevoTurno(usuario)
    await completarTurno(usuario, { paciente: '2', prestacion: 'Limpieza · 45 min', hora: '15:00' })
    servidor.vencerAccess()
    servidor.invalidarRefresh()

    await usuario.click(botonCrear())

    expect((await screen.findByRole('status')).textContent).toBe(AVISO_SESION_TERMINADA)
    expect(screen.getByTestId('lugar').textContent).toBe('/ingresar')
    expect(screen.queryByText(MENSAJE_DE_CONEXION)).toBeNull()
    expect(servidor.turnosActuales()).toHaveLength(3)
  })
})
