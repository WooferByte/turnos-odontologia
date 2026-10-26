import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { App } from '../../App'
import { CLAVE_DE_SESION } from '../../shared/api/sesion'
import {
  BLOQUEO_DE_VACACIONES,
  BLOQUEO_FERIADO,
  EMAIL_ACTIVA,
  EMAIL_DUENO,
  EMAIL_RECEPCIONISTA,
  PROFESIONAL_INACTIVO,
  PROFESIONALES_DE_PARTIDA,
  SILLON_INACTIVO,
  SILLONES_DE_PARTIDA,
  TURNOS_DEL_2_DE_NOVIEMBRE,
  USUARIOS_DE_PARTIDA,
  USUARIO_DUENO,
  crearServidorFalso,
  type ServidorFalso,
} from '../../test/servidorFalso'

type Usuario = ReturnType<typeof userEvent.setup>

const MENSAJE_DE_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'
const AVISO_SESION_TERMINADA = 'Tu sesión terminó. Iniciá sesión de nuevo.'
const SIN_AFECTADOS = 'Bloqueo creado. No hay turnos activos en ese horario.'
const MENSAJE_RN_AG_17 = 'El bloqueo tiene que terminar después de empezar (RN-AG-17).'
const MENSAJE_INCOMPLETO = 'Completá alcance, desde, hasta y motivo.'
const MENSAJE_SIN_PERMISO = 'Tu usuario no tiene permiso para modificar los bloqueos (RN-AU-05).'
const RUTA = '/api/bloqueos'

function LugarActual() {
  const ubicacion = useLocation()
  return <p data-testid="lugar">{ubicacion.pathname}</p>
}

/** Monta la aplicación con una sesión guardada (como tras recargar). */
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

async function abrirBloqueos(servidor: ServidorFalso, email = EMAIL_ACTIVA): Promise<Usuario> {
  const usuario = await abrirPanel(servidor, '/panel/bloqueos', email)
  await screen.findByRole('region', { name: 'Nuevo bloqueo' })
  return usuario
}

function escribirFecha(etiqueta: 'Desde' | 'Hasta', valor: string): void {
  fireEvent.change(screen.getByLabelText(etiqueta), { target: { value: valor } })
}

async function elegirAlcance(usuario: Usuario, alcance: string, recurso: string | null = null): Promise<void> {
  await usuario.selectOptions(screen.getByLabelText('Alcance'), alcance)
  if (recurso !== null) {
    const nombre = alcance === 'Un profesional' ? 'Profesional' : 'Sillón'
    await usuario.selectOptions(screen.getByLabelText(nombre), recurso)
  }
}

async function completar(
  usuario: Usuario,
  alcance: string,
  recurso: string | null,
  desde: string,
  hasta: string,
  motivo: string,
): Promise<void> {
  await elegirAlcance(usuario, alcance, recurso)
  escribirFecha('Desde', desde)
  escribirFecha('Hasta', hasta)
  const campo = screen.getByLabelText('Motivo')
  await usuario.clear(campo)
  if (motivo !== '') fireEvent.change(campo, { target: { value: motivo } })
}

/** Todo el consultorio el 23/11/2026, el formulario más simple. */
async function completarFeriado(usuario: Usuario): Promise<void> {
  await completar(usuario, 'Todo el consultorio', null, '2026-11-23T00:00', '2026-11-24T00:00', 'Feriado')
}

function botonBloquear(): HTMLButtonElement {
  return screen.getByRole<HTMLButtonElement>('button', { name: 'Bloquear' })
}

/** Las filas de la tabla de bloqueos como textos de celda, sin la columna de acciones. */
function filasDeBloqueos(): string[][] {
  return screen
    .queryAllByRole('row')
    .slice(1)
    .map((fila) =>
      within(fila)
        .getAllByRole('cell')
        .slice(0, 4)
        .map((celda) => celda.textContent ?? ''),
    )
}

function filaDe(motivo: string): HTMLElement {
  const fila = screen.getAllByRole('row').find((f) => within(f).queryByText(motivo) !== null)
  if (fila === undefined) throw new Error(`No hay una fila con el motivo ${motivo}`)
  return fila
}

function botonEliminarDe(motivo: string): HTMLButtonElement {
  return within(filaDe(motivo)).getByRole<HTMLButtonElement>('button', { name: 'Eliminar bloqueo' })
}

const FERIADO_EN_LISTA = ['Todo el consultorio', '23/11/2026 00:00', '24/11/2026 00:00', 'Feriado']
const VACACIONES_EN_LISTA = ['Profesional: Dra. Demo Ficticia', '09/11/2026 00:00', '14/11/2026 00:00', 'Vacaciones']

function conSesionLimpia(): void {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })
}

describe('PaginaBloqueos: la lista', () => {
  conSesionLimpia()

  it('US-003 CA-1: la odontóloga ve los bloqueos', async () => {
    const servidor = crearServidorFalso({ bloqueos: [BLOQUEO_FERIADO, BLOQUEO_DE_VACACIONES] })
    const usuario = await abrirPanel(servidor)
    await screen.findByText('Panel del consultorio')

    await usuario.click(screen.getByRole('link', { name: 'Bloqueos' }))

    await screen.findByRole('table')
    expect(screen.getByTestId('lugar').textContent).toBe('/panel/bloqueos')
    expect(filasDeBloqueos()).toEqual([VACACIONES_EN_LISTA, FERIADO_EN_LISTA])
    expect(screen.getByText('Fechas y horas del consultorio (America/Argentina/Buenos_Aires).')).toBeDefined()
    expect(
      screen.getByText('Un bloqueo impide dar turnos en ese horario (RN-AG-04b). Los turnos que ya estaban no se cancelan.'),
    ).toBeDefined()
    expect(servidor.llamadas('GET', RUTA)).toBe(1)
    expect(servidor.llamadas('GET', '/api/profesionales')).toBe(1)
    expect(servidor.llamadas('GET', '/api/sillones')).toBe(1)
  })

  it('US-003 CA-1: sin bloqueos, y la recepcionista y el dueño ven la lista', async () => {
    const catalogo = [...USUARIOS_DE_PARTIDA, USUARIO_DUENO]
    for (const email of [EMAIL_RECEPCIONISTA, EMAIL_DUENO]) {
      sessionStorage.clear()
      await abrirBloqueos(crearServidorFalso({ usuarios: catalogo }), email)

      expect(screen.getByText('No hay bloqueos cargados.')).toBeDefined()
      expect(screen.queryByRole('table')).toBeNull()
      expect(screen.getByRole('button', { name: 'Bloquear' })).toBeDefined()
      cleanup()
    }
    sessionStorage.clear()
    await abrirBloqueos(crearServidorFalso({ bloqueos: [BLOQUEO_FERIADO], usuarios: catalogo }), EMAIL_RECEPCIONISTA)
    expect(filasDeBloqueos()).toEqual([FERIADO_EN_LISTA])
  })

  it('US-003 CA-1: mientras carga y sin conexión', async () => {
    const servidor = crearServidorFalso({ bloqueos: [BLOQUEO_FERIADO] })
    const liberar = servidor.retener(RUTA)
    const usuario = await abrirPanel(servidor, '/panel/bloqueos')

    expect(await screen.findByText('Cargando bloqueos…')).toBeDefined()
    expect(screen.queryByRole('row')).toBeNull()
    servidor.caerse()
    liberar()

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain(MENSAJE_DE_CONEXION)
    expect(screen.queryByText('Cargando bloqueos…')).toBeNull()
    servidor.recuperar()
    await usuario.click(screen.getByRole('button', { name: 'Reintentar' }))

    await screen.findByRole('table')
    expect(filasDeBloqueos()).toEqual([FERIADO_EN_LISTA])
    expect(screen.queryByRole('alert')).toBeNull()
  })
})

describe('PaginaBloqueos: crear', () => {
  conSesionLimpia()

  it('US-003 CA-1: bloquear todo el consultorio por un feriado', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirBloqueos(servidor)

    await completarFeriado(usuario)
    await usuario.click(botonBloquear())

    expect(await screen.findByText(SIN_AFECTADOS)).toBeDefined()
    expect(servidor.llamadas('POST', RUTA)).toBe(1)
    expect(servidor.cuerpos('POST', RUTA)).toEqual([
      { inicio: '2026-11-23T03:00:00Z', fin: '2026-11-24T03:00:00Z', motivo: 'Feriado' },
    ])
    await waitFor(() => expect(filasDeBloqueos()).toEqual([FERIADO_EN_LISTA]))
    expect(screen.queryByText('No hay bloqueos cargados.')).toBeNull()
    expect((screen.getByLabelText('Motivo') as HTMLInputElement).value).toBe('')
  })

  it('US-003 CA-2: bloquear al profesional sobre dos turnos activos los muestra sin cancelarlos', async () => {
    const servidor = crearServidorFalso({ turnos: TURNOS_DEL_2_DE_NOVIEMBRE })
    const usuario = await abrirBloqueos(servidor)

    await completar(usuario, 'Un profesional', 'Dra. Demo Ficticia', '2026-11-02T09:00', '2026-11-02T13:00', 'Ausencia')
    await usuario.click(botonBloquear())

    expect(
      await screen.findByText(
        'Bloqueo creado. Hay 2 turnos activos en ese horario: no se cancelaron, hay que reprogramarlos o cancelarlos.',
      ),
    ).toBeDefined()
    expect(servidor.cuerpos('POST', RUTA)).toEqual([
      { inicio: '2026-11-02T12:00:00Z', fin: '2026-11-02T16:00:00Z', motivo: 'Ausencia', profesional_id: 1 },
    ])
    const afectados = within(screen.getByRole('status')).getAllByRole('listitem')
    expect(afectados.map((fila) => fila.textContent)).toEqual([
      'Turno 7 · 02/11/2026 10:00 a 10:30reservado',
      'Turno 8 · 02/11/2026 11:00 a 11:30confirmado',
    ])
    expect(within(afectados[0] as HTMLElement).getByText('reservado')).toBeDefined()
    expect(within(afectados[1] as HTMLElement).getByText('confirmado')).toBeDefined()
  })

  it('US-003 CA-1: bloquear un sillón manda sillon_id y no profesional_id', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirBloqueos(servidor)

    await completar(usuario, 'Un sillón', 'Sillón 1', '2026-11-23T08:30', '2026-11-23T12:00', 'Mantenimiento')
    await usuario.click(botonBloquear())

    await screen.findByText(SIN_AFECTADOS)
    expect(servidor.cuerpos('POST', RUTA)).toEqual([
      { inicio: '2026-11-23T11:30:00Z', fin: '2026-11-23T15:00:00Z', motivo: 'Mantenimiento', sillon_id: 1 },
    ])
    await waitFor(() =>
      expect(filasDeBloqueos()).toEqual([['Sillón: Sillón 1', '23/11/2026 08:30', '23/11/2026 12:00', 'Mantenimiento']]),
    )
  })

  it('US-003 CA-1: con un campo obligatorio vacío no se manda nada', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirBloqueos(servidor)

    await completar(usuario, 'Un sillón', null, '2026-11-23T00:00', '2026-11-24T00:00', 'Feriado')
    await usuario.click(botonBloquear())
    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_INCOMPLETO)
    expect(servidor.llamadas('POST', RUTA)).toBe(0)

    await completar(usuario, 'Un sillón', 'Sillón 1', '2026-11-23T00:00', '2026-11-24T00:00', '')
    await usuario.click(botonBloquear())
    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_INCOMPLETO)
    expect(servidor.llamadas('POST', RUTA)).toBe(0)
  })

  it('US-003 CA-1: sin conexión al crear se conserva lo cargado', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirBloqueos(servidor)
    await completarFeriado(usuario)
    servidor.caerse()

    await usuario.click(botonBloquear())

    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_DE_CONEXION)
    expect(screen.queryByRole('button', { name: 'Reintentar' })).toBeNull()
    expect(screen.queryByText(SIN_AFECTADOS)).toBeNull()
    expect((screen.getByLabelText('Desde') as HTMLInputElement).value).toBe('2026-11-23T00:00')
    expect((screen.getByLabelText('Hasta') as HTMLInputElement).value).toBe('2026-11-24T00:00')
    expect((screen.getByLabelText('Motivo') as HTMLInputElement).value).toBe('Feriado')
    expect(botonBloquear().disabled).toBe(false)
  })

  it('US-003 CA-1: pulsar «Bloquear» dos veces manda un solo pedido', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirBloqueos(servidor)
    await completarFeriado(usuario)
    const liberar = servidor.retener(RUTA)

    await usuario.click(botonBloquear())
    await waitFor(() => expect(botonBloquear().disabled).toBe(true))
    await usuario.click(botonBloquear())

    expect(servidor.llamadas('POST', RUTA)).toBe(1)
    liberar()
    expect(await screen.findByText(SIN_AFECTADOS)).toBeDefined()
    expect(servidor.llamadas('POST', RUTA)).toBe(1)
    expect(botonBloquear().disabled).toBe(false)
  })

  it('US-003 CA-1: el selector de recurso ofrece solo los activos', async () => {
    const servidor = crearServidorFalso({
      profesionales: [...PROFESIONALES_DE_PARTIDA, PROFESIONAL_INACTIVO],
      sillones: [...SILLONES_DE_PARTIDA, SILLON_INACTIVO],
    })
    const usuario = await abrirBloqueos(servidor)
    const opciones = (etiqueta: string) =>
      within(screen.getByLabelText(etiqueta))
        .getAllByRole('option')
        .map((o) => o.textContent)
        .filter((texto) => texto !== 'Elegí una opción')

    await usuario.selectOptions(screen.getByLabelText('Alcance'), 'Un profesional')
    expect(opciones('Profesional')).toEqual(['Dra. Demo Ficticia'])
    await usuario.selectOptions(screen.getByLabelText('Alcance'), 'Un sillón')

    expect(opciones('Sillón')).toEqual(['Sillón 1'])
    expect(screen.queryByLabelText('Profesional')).toBeNull()
  })
})

describe('PaginaBloqueos: eliminar', () => {
  conSesionLimpia()

  it('US-003 CA-1: la odontóloga elimina un bloqueo', async () => {
    const servidor = crearServidorFalso({ bloqueos: [BLOQUEO_FERIADO, BLOQUEO_DE_VACACIONES] })
    const usuario = await abrirBloqueos(servidor)

    await usuario.click(botonEliminarDe('Feriado'))

    expect(await screen.findByText('Bloqueo eliminado.')).toBeDefined()
    expect(servidor.llamadas('DELETE', '/api/bloqueos/2')).toBe(1)
    expect(filasDeBloqueos()).toEqual([VACACIONES_EN_LISTA])
    await usuario.click(botonEliminarDe('Vacaciones'))
    expect(await screen.findByText('No hay bloqueos cargados.')).toBeDefined()
    expect(servidor.bloqueosActuales()).toEqual([])
  })

  it('US-003 CA-1: pulsar «Eliminar» dos veces manda un solo pedido', async () => {
    const servidor = crearServidorFalso({ bloqueos: [BLOQUEO_FERIADO] })
    const usuario = await abrirBloqueos(servidor)
    const liberar = servidor.retener('/api/bloqueos/2')

    await usuario.click(botonEliminarDe('Feriado'))
    await waitFor(() => expect(botonEliminarDe('Feriado').disabled).toBe(true))
    await usuario.click(botonEliminarDe('Feriado'))

    expect(servidor.llamadas('DELETE', '/api/bloqueos/2')).toBe(1)
    liberar()
    expect(await screen.findByText('Bloqueo eliminado.')).toBeDefined()
    expect(screen.queryByText('El bloqueo ya no existe (RN-GL-04).')).toBeNull()
    expect(servidor.llamadas('DELETE', '/api/bloqueos/2')).toBe(1)
  })

  it('US-003 CA-1: sin conexión al eliminar el bloqueo sigue en la lista', async () => {
    const servidor = crearServidorFalso({ bloqueos: [BLOQUEO_FERIADO] })
    const usuario = await abrirBloqueos(servidor)
    servidor.caerse()

    await usuario.click(botonEliminarDe('Feriado'))

    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_DE_CONEXION)
    expect(screen.queryByRole('button', { name: 'Reintentar' })).toBeNull()
    expect(screen.queryByText('Bloqueo eliminado.')).toBeNull()
    expect(filasDeBloqueos()).toEqual([FERIADO_EN_LISTA])
    expect(botonEliminarDe('Feriado').disabled).toBe(false)
  })
})

describe('PaginaBloqueos: rechazos y sesión', () => {
  conSesionLimpia()

  it('US-003 CA-1: hasta antes que desde se manda y vuelve con RN-AG-17', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirBloqueos(servidor)

    await completar(usuario, 'Todo el consultorio', null, '2026-11-02T15:00', '2026-11-02T13:00', 'Ausencia')
    await usuario.click(botonBloquear())

    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_RN_AG_17)
    expect(servidor.llamadas('POST', RUTA)).toBe(1)
    expect(screen.getByLabelText('Hasta').getAttribute('aria-invalid')).toBe('true')
    expect((screen.getByLabelText('Desde') as HTMLInputElement).value).toBe('2026-11-02T15:00')
    expect((screen.getByLabelText('Hasta') as HTMLInputElement).value).toBe('2026-11-02T13:00')
    expect((screen.getByLabelText('Motivo') as HTMLInputElement).value).toBe('Ausencia')
    expect(screen.queryByText(/Bloqueo creado/)).toBeNull()
    escribirFecha('Hasta', '2026-11-02T17:00')
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull())
    expect(screen.getByLabelText('Hasta').getAttribute('aria-invalid')).toBeNull()
  })

  it('US-003 CA-1: un motivo demasiado largo vuelve con «Revisá los datos del bloqueo.»', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirBloqueos(servidor)

    await completar(usuario, 'Todo el consultorio', null, '2026-11-23T00:00', '2026-11-24T00:00', 'x'.repeat(201))
    await usuario.click(botonBloquear())

    expect((await screen.findByRole('alert')).textContent).toContain('Revisá los datos del bloqueo.')
    expect(servidor.llamadas('POST', RUTA)).toBe(1)
    expect((screen.getByLabelText('Motivo') as HTMLInputElement).value).toHaveLength(201)
    expect(screen.queryByText(/Bloqueo creado/)).toBeNull()
  })

  it('US-003 CA-1: un motivo de 200 caracteres se acepta', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirBloqueos(servidor)

    await completar(usuario, 'Todo el consultorio', null, '2026-11-23T00:00', '2026-11-24T00:00', 'x'.repeat(200))
    await usuario.click(botonBloquear())

    expect(await screen.findByText(SIN_AFECTADOS)).toBeDefined()
    expect(servidor.bloqueosActuales()).toHaveLength(1)
  })

  it('US-003 CA-1: la recepcionista intenta crear y eliminar', async () => {
    const servidor = crearServidorFalso({ bloqueos: [BLOQUEO_FERIADO] })
    const usuario = await abrirBloqueos(servidor, EMAIL_RECEPCIONISTA)
    const refrescosAntes = servidor.llamadas('POST', '/api/auth/refresh')

    await completar(usuario, 'Un profesional', 'Dra. Demo Ficticia', '2026-11-09T00:00', '2026-11-10T00:00', 'Curso')
    await usuario.click(botonBloquear())
    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_SIN_PERMISO)
    await usuario.click(botonEliminarDe('Feriado'))

    await waitFor(() => expect(servidor.llamadas('DELETE', '/api/bloqueos/2')).toBe(1))
    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_SIN_PERMISO)
    expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(refrescosAntes)
    expect(screen.getByTestId('lugar').textContent).toBe('/panel/bloqueos')
    expect(filasDeBloqueos()).toEqual([FERIADO_EN_LISTA])
    expect(servidor.bloqueosActuales()).toHaveLength(1)
  })

  it('US-003 CA-1: un bloqueo que ya no existe y un profesional que ya no está', async () => {
    const servidor = crearServidorFalso({ bloqueos: [BLOQUEO_FERIADO] })
    const usuario = await abrirBloqueos(servidor)
    servidor.quitarBloqueo(2)

    await usuario.click(botonEliminarDe('Feriado'))

    expect((await screen.findByRole('alert')).textContent).toContain('El bloqueo ya no existe (RN-GL-04).')
    await waitFor(() => expect(servidor.llamadas('GET', RUTA)).toBe(2))
    await waitFor(() => expect(screen.queryByRole('table')).toBeNull())
    await completar(usuario, 'Un profesional', 'Dra. Demo Ficticia', '2026-11-09T00:00', '2026-11-10T00:00', 'Curso')
    servidor.quitarProfesional(1)
    await usuario.click(botonBloquear())

    expect((await screen.findByRole('alert')).textContent).toContain(
      'El profesional o el sillón elegido ya no está disponible (RN-GL-04).',
    )
    await waitFor(() => expect(servidor.llamadas('GET', '/api/profesionales')).toBe(2))
    expect(servidor.llamadas('GET', '/api/sillones')).toBe(2)
    expect(
      within(screen.getByLabelText('Profesional'))
        .getAllByRole('option')
        .map((o) => o.textContent),
    ).toEqual(['Elegí una opción'])
    expect((screen.getByLabelText('Motivo') as HTMLInputElement).value).toBe('Curso')
  })

  it('US-092 CA-1: una sesión irrenovable al crear un bloqueo', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirBloqueos(servidor)
    await completarFeriado(usuario)
    servidor.vencerAccess()
    servidor.invalidarRefresh()

    await usuario.click(botonBloquear())

    expect((await screen.findByRole('status')).textContent).toBe(AVISO_SESION_TERMINADA)
    expect(screen.getByTestId('lugar').textContent).toBe('/ingresar')
    expect(screen.queryByText(MENSAJE_DE_CONEXION)).toBeNull()
    expect(servidor.bloqueosActuales()).toEqual([])
  })
})
