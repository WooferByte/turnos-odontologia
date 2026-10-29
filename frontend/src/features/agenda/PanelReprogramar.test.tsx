import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { App } from '../../App'
import { CLAVE_DE_SESION } from '../../shared/api/sesion'
import {
  EMAIL_ACTIVA as EMAIL_ODONTOLOGA,
  EMAIL_DUENO,
  EMAIL_RECEPCIONISTA,
  PRESTACIONES_DE_PARTIDA,
  TURNOS_DE_LA_AGENDA,
  USUARIOS_DE_PARTIDA,
  USUARIO_DUENO,
  crearServidorFalso,
  type TurnoFalso,
  type OpcionesDelServidorFalso,
  type ServidorFalso,
} from '../../test/servidorFalso'

type Usuario = ReturnType<typeof userEvent.setup>

function LugarActual() {
  const ubicacion = useLocation()
  return <p data-testid="lugar">{ubicacion.pathname}</p>
}

/** El falso con las prestaciones de la demo y los tres turnos del 2 de noviembre. */
function falso(opciones: OpcionesDelServidorFalso = {}): ServidorFalso {
  return crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA, turnos: TURNOS_DE_LA_AGENDA, ...opciones })
}

/** Monta la aplicación con una sesión guardada y espera la agenda del 2 de noviembre. */
async function abrirAgenda(servidor: ServidorFalso, email = EMAIL_RECEPCIONISTA): Promise<Usuario> {
  sessionStorage.setItem(CLAVE_DE_SESION, JSON.stringify({ refresh: servidor.emitirSesion(email).refresh }))
  render(
    <MemoryRouter initialEntries={['/panel/agenda']}>
      <LugarActual />
      <App fetch={servidor.fetch} />
    </MemoryRouter>,
  )
  await screen.findByText('lunes 2 de noviembre de 2026')
  return userEvent.setup()
}

const ANA = 'Reprogramar el turno de Ana Ejemplo, 09:00'
const BRUNO = 'Reprogramar el turno de Bruno Ficticio, 10:00'
const CARLA = 'Reprogramar el turno de Carla Inventada, 11:00'
const MENSAJE_DE_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'

function botonDeReprogramar(nombre: string): HTMLElement {
  return screen.getByRole('button', { name: nombre })
}

async function abrirReprogramar(usuario: Usuario, nombre = ANA): Promise<HTMLElement> {
  await usuario.click(botonDeReprogramar(nombre))
  return screen.findByRole('complementary', { name: 'Reprogramar turno' })
}

function cambiarCampo(etiqueta: string, valor: string): void {
  fireEvent.change(screen.getByLabelText(etiqueta), { target: { value: valor } })
}

function botonReprogramar(): HTMLButtonElement {
  return screen.getByRole('button', { name: 'Reprogramar' })
}

function totalDePeticiones(servidor: ServidorFalso): number {
  return servidor.rutasPedidas().reduce((suma, ruta) => suma + servidor.peticiones(ruta), 0)
}

function filasDeLaAgenda(): string[][] {
  return screen
    .getAllByRole('row')
    .slice(1)
    .map((fila) => within(fila).getAllByRole('cell').slice(0, 4).map((celda) => celda.textContent ?? ''))
}

function filasSeleccionadas(): string[] {
  return [...document.querySelectorAll('tr.fila-seleccionada')].map((fila) => fila.textContent ?? '')
}

beforeEach(() => {
  sessionStorage.clear()
})

afterEach(() => {
  cleanup()
})

describe('PanelReprogramar: reprogramar desde la agenda', () => {
  it('REP-6a: la recepcionista mueve un turno y lo ve en su nuevo horario', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    const antes = totalDePeticiones(servidor)

    const panel = await abrirReprogramar(usuario)

    expect(within(panel).getByRole('heading', { name: 'Reprogramar turno' })).toBeDefined()
    expect(within(panel).getByText('Ana Ejemplo · Consulta / control')).toBeDefined()
    expect(within(panel).getByText('Ahora: lunes 2 de noviembre de 2026, 09:00 – 09:30')).toBeDefined()
    expect(within(panel).getByText('Fecha y hora del consultorio.')).toBeDefined()
    expect((screen.getByLabelText('Fecha') as HTMLInputElement).value).toBe('2026-11-02')
    expect((screen.getByLabelText('Hora') as HTMLInputElement).value).toBe('09:00')
    expect((screen.getByLabelText('Duración (minutos)') as HTMLInputElement).value).toBe('30')
    expect(within(panel).getByText('Múltiplo de 5 minutos.')).toBeDefined()
    expect(within(panel).getByText('Termina a las 09:30.')).toBeDefined()
    expect(totalDePeticiones(servidor)).toBe(antes)
    expect(document.activeElement).toBe(screen.getByLabelText('Fecha'))
    expect(filasSeleccionadas()).toHaveLength(1)
    expect(filasSeleccionadas()[0]).toContain('Ana Ejemplo')

    cambiarCampo('Hora', '12:30')
    expect(screen.getByText('Termina a las 13:00.')).toBeDefined()
    await usuario.click(botonReprogramar())

    expect(await screen.findByText('Turno reprogramado.')).toBeDefined()
    expect(servidor.llamadas('PATCH', '/api/turnos/11')).toBe(1)
    expect(servidor.cuerpos('PATCH', '/api/turnos/11')).toEqual([{ inicio: '2026-11-02T15:30:00Z', duracion_minutos: 30 }])
    expect(screen.queryByRole('complementary', { name: 'Reprogramar turno' })).toBeNull()
    expect(servidor.peticiones('/api/turnos?fecha=2026-11-02')).toBe(1)
    expect(filasDeLaAgenda()).toEqual([
      ['10:00 – 10:45', 'Bruno Ficticio', 'Limpieza', 'Reservado'],
      ['11:00 – 12:00', 'Carla Inventada', 'Obturación', 'Confirmado'],
      ['12:30 – 13:00', 'Ana Ejemplo', 'Consulta / control', 'Reservado'],
    ])
  })
})

function turnoExtra(id: number, hora: number, estado: string): TurnoFalso {
  const inicio = `2026-11-02T${String(hora + 3).padStart(2, '0')}:00:00Z`
  const fin = `2026-11-02T${String(hora + 3).padStart(2, '0')}:30:00Z`
  return { id, inicio, fin, estado, profesional_id: 1, sillon_id: 1, paciente_id: 2, prestacion_id: 1 }
}

describe('PanelReprogramar: bordes', () => {
  it('REP-6b: a otro día que cruza la medianoche UTC', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor, EMAIL_ODONTOLOGA)
    await abrirReprogramar(usuario, BRUNO)

    cambiarCampo('Fecha', '2026-11-03')
    cambiarCampo('Hora', '22:00')

    expect(screen.getByText('Termina a las 22:45.')).toBeDefined()
    await usuario.click(botonReprogramar())
    expect(await screen.findByText('Turno reprogramado.')).toBeDefined()
    expect(servidor.cuerpos('PATCH', '/api/turnos/12')).toEqual([{ inicio: '2026-11-04T01:00:00Z', duracion_minutos: 45 }])
    await screen.findByText('martes 3 de noviembre de 2026')
    expect(servidor.peticiones('/api/turnos?fecha=2026-11-03')).toBe(1)
    expect(servidor.peticiones('/api/turnos?fecha=2026-11-04')).toBe(0)
    expect(filasDeLaAgenda()).toEqual([['22:00 – 22:45', 'Bruno Ficticio', 'Limpieza', 'Reservado']])
  })

  it('REP-6b: solo la duración', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor, EMAIL_ODONTOLOGA)
    await abrirReprogramar(usuario, CARLA)

    cambiarCampo('Duración (minutos)', '90')

    expect(screen.getByText('Termina a las 12:30.')).toBeDefined()
    await usuario.click(botonReprogramar())
    expect(await screen.findByText('Turno reprogramado.')).toBeDefined()
    expect(servidor.cuerpos('PATCH', '/api/turnos/13')).toEqual([{ inicio: '2026-11-02T14:00:00Z', duracion_minutos: 90 }])
    await screen.findByText('11:00 – 12:30')
    expect(filasDeLaAgenda()).toEqual([
      ['09:00 – 09:30', 'Ana Ejemplo', 'Consulta / control', 'Reservado'],
      ['10:00 – 10:45', 'Bruno Ficticio', 'Limpieza', 'Reservado'],
      ['11:00 – 12:30', 'Carla Inventada', 'Obturación', 'Confirmado'],
    ])
  })

  it('REP-6c: un solo panel a la vez', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirReprogramar(usuario)

    await usuario.click(screen.getByRole('button', { name: 'Historial del turno de Ana Ejemplo, 09:00' }))

    await screen.findByRole('complementary', { name: 'Historial del turno' })
    expect(screen.queryByRole('complementary', { name: 'Reprogramar turno' })).toBeNull()
    await usuario.click(screen.getByRole('button', { name: 'Nuevo turno' }))
    await screen.findByRole('complementary', { name: 'Nuevo turno' })
    expect(screen.queryByRole('complementary', { name: 'Historial del turno' })).toBeNull()
    await abrirReprogramar(usuario, BRUNO)
    expect(screen.queryByRole('complementary', { name: 'Nuevo turno' })).toBeNull()
    expect(filasSeleccionadas()).toHaveLength(1)
    expect(filasSeleccionadas()[0]).toContain('Bruno Ficticio')
  })

  it('REP-6c: cambiar de día cierra el panel sin mandar nada', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirReprogramar(usuario)

    await usuario.click(screen.getByRole('button', { name: 'Día siguiente' }))

    await screen.findByText('martes 3 de noviembre de 2026')
    expect(screen.queryByRole('complementary', { name: 'Reprogramar turno' })).toBeNull()
    expect(servidor.llamadas('PATCH', '/api/turnos/11')).toBe(0)
  })

  it('REP-6c: Cancelar devuelve el foco al botón de la fila', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    const antes = totalDePeticiones(servidor)
    await abrirReprogramar(usuario)

    await usuario.click(screen.getByRole('button', { name: 'Cancelar' }))

    expect(screen.queryByRole('complementary', { name: 'Reprogramar turno' })).toBeNull()
    expect(document.activeElement).toBe(botonDeReprogramar(ANA))
    expect(filasSeleccionadas()).toEqual([])
    expect(totalDePeticiones(servidor)).toBe(antes)
  })

  it('REP-6c: Cerrar devuelve el foco al botón de la fila', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirReprogramar(usuario)

    await usuario.click(screen.getByRole('button', { name: 'Cerrar' }))

    expect(screen.queryByRole('complementary', { name: 'Reprogramar turno' })).toBeNull()
    expect(document.activeElement).toBe(botonDeReprogramar(ANA))
    expect(filasSeleccionadas()).toEqual([])
    expect(servidor.llamadas('PATCH', '/api/turnos/11')).toBe(0)
  })

  it('REP-6c: los turnos no activos no tienen Reprogramar', async () => {
    const servidor = falso({
      turnos: [
        ...TURNOS_DE_LA_AGENDA,
        turnoExtra(14, 12, 'cancelado_paciente'),
        turnoExtra(15, 13, 'atendido'),
        turnoExtra(16, 14, 'ausente'),
        turnoExtra(17, 15, 'vencido'),
        turnoExtra(18, 16, 'pendiente_aprobacion'),
        turnoExtra(19, 17, 'pendiente_sena'),
      ],
    })
    await abrirAgenda(servidor)

    const filas = screen.getAllByRole('row').slice(1)

    expect(filas).toHaveLength(9)
    expect(filas.map((fila) => within(fila).queryByRole('button', { name: /^Reprogramar/ }) !== null)).toEqual([
      true, true, true, false, false, false, false, true, true,
    ])
    expect(filas.every((fila) => within(fila).queryByRole('button', { name: /^Historial/ }) !== null)).toBe(true)
  })

  it('REP-6d: la recarga falla después del 200', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirReprogramar(usuario)
    cambiarCampo('Hora', '12:30')
    servidor.fallarRuta('/api/turnos?fecha=2026-11-02', 'red')

    await usuario.click(botonReprogramar())

    expect(await screen.findByText('Turno reprogramado.')).toBeDefined()
    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_DE_CONEXION)
    expect(screen.queryByRole('complementary', { name: 'Reprogramar turno' })).toBeNull()
    expect(servidor.llamadas('PATCH', '/api/turnos/11')).toBe(1)

    servidor.repararRuta('/api/turnos?fecha=2026-11-02')
    await usuario.click(screen.getByRole('button', { name: 'Reintentar' }))

    await screen.findByText('12:30 – 13:00')
    expect(servidor.llamadas('PATCH', '/api/turnos/11')).toBe(1)
    expect(servidor.peticiones('/api/turnos?fecha=2026-11-02')).toBe(2)
    expect(filasDeLaAgenda().at(-1)).toEqual(['12:30 – 13:00', 'Ana Ejemplo', 'Consulta / control', 'Reservado'])
  })
})

/** Lo cargado en el panel después de un rechazo: sigue abierto, sin «Turno reprogramado.» y con el turno como estaba. */
function comprobarQueNoCambio(servidor: ServidorFalso, hora: string, duracion: string): void {
  expect(screen.getByRole('complementary', { name: 'Reprogramar turno' })).toBeDefined()
  expect((screen.getByLabelText('Hora') as HTMLInputElement).value).toBe(hora)
  expect((screen.getByLabelText('Duración (minutos)') as HTMLInputElement).value).toBe(duracion)
  expect(screen.queryByText('Turno reprogramado.')).toBeNull()
  expect(servidor.llamadas('PATCH', '/api/turnos/11')).toBe(1)
  expect(servidor.turnosActuales().find((t) => t.id === 11)?.inicio).toBe('2026-11-02T12:00:00Z')
}

describe('PanelReprogramar: los rechazos', () => {
  it('REP-7a: sobre otro turno activo muestra los dos códigos y el turno no cambia', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirReprogramar(usuario)
    cambiarCampo('Hora', '10:15')

    await usuario.click(botonReprogramar())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain('El profesional y el sillón ya tienen un turno activo en ese horario (RN-AG-05, RN-AG-08).')
    expect(aviso.textContent).toContain('El turno no cambió.')
    expect(servidor.cuerpos('PATCH', '/api/turnos/11')).toEqual([{ inicio: '2026-11-02T13:15:00Z', duracion_minutos: 30 }])
    comprobarQueNoCambio(servidor, '10:15', '30')
    expect(filasDeLaAgenda()[0]).toEqual(['09:00 – 09:30', 'Ana Ejemplo', 'Consulta / control', 'Reservado'])
  })

  it.each([
    [422, ['RN-AG-01'], '42', 'La duración debe ser mayor que 0 y múltiplo de 5 minutos (RN-AG-01).'],
    [422, ['RN-AG-04'], '30', 'El turno no cae dentro del horario de atención del profesional (RN-AG-04).'],
    [422, ['RN-AG-04b'], '30', 'Ese horario está bloqueado (RN-AG-04b).'],
    [422, ['RN-AG-10d'], '30', 'El turno no puede pasar de la medianoche del consultorio (RN-AG-10d).'],
    [409, ['RN-AG-18'], '30', 'Este turno ya no se puede reprogramar por su estado (RN-AG-18).'],
    [404, ['RN-GL-04'], '30', 'El turno ya no existe (RN-GL-04).'],
    [403, ['RN-AU-05'], '30', 'Tu usuario no tiene permiso para reprogramar turnos (RN-AU-05).'],
  ])('REP-7b: el %i con %j se ve como «%s» (duración %s)', async (estado, codigos, duracion, texto) => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirReprogramar(usuario)
    cambiarCampo('Hora', '12:30')
    cambiarCampo('Duración (minutos)', duracion)
    servidor.responderAlReprogramar(estado, codigos)
    const refrescosAntes = servidor.llamadas('POST', '/api/auth/refresh')

    await usuario.click(botonReprogramar())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain(texto)
    expect(aviso.textContent).toContain('El turno no cambió.')
    expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(refrescosAntes)
    expect(screen.getByTestId('lugar').textContent).toBe('/panel/agenda')
    comprobarQueNoCambio(servidor, '12:30', duracion)
  })

  it('REP-7c: un campo vacío no manda nada', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirReprogramar(usuario)
    cambiarCampo('Hora', '')

    await usuario.click(botonReprogramar())

    expect((await screen.findByRole('alert')).textContent).toContain('Completá fecha, hora y duración.')
    expect(servidor.llamadas('PATCH', '/api/turnos/11')).toBe(0)
  })

  it('REP-7c: una duración no numérica no manda nada', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirReprogramar(usuario)
    cambiarCampo('Duración (minutos)', 'media')

    await usuario.click(botonReprogramar())

    expect((await screen.findByRole('alert')).textContent).toContain('Completá fecha, hora y duración.')
    expect(screen.queryByText(/Termina a las/)).toBeNull()
    expect(servidor.llamadas('PATCH', '/api/turnos/11')).toBe(0)
  })

  it('REP-7c: sin cambios no manda nada', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirReprogramar(usuario)

    await usuario.click(botonReprogramar())

    expect((await screen.findByRole('alert')).textContent).toContain('No cambiaste la fecha, la hora ni la duración.')
    expect(servidor.llamadas('PATCH', '/api/turnos/11')).toBe(0)
    expect(screen.queryByText('Turno reprogramado.')).toBeNull()
  })

  it('REP-7c: Cancelar no manda nada', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirReprogramar(usuario)
    cambiarCampo('Hora', '12:30')

    await usuario.click(screen.getByRole('button', { name: 'Cancelar' }))

    expect(screen.queryByRole('complementary', { name: 'Reprogramar turno' })).toBeNull()
    expect(servidor.llamadas('PATCH', '/api/turnos/11')).toBe(0)
  })

  it('REP-7c: el doble clic manda un solo PATCH', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirReprogramar(usuario)
    cambiarCampo('Hora', '12:30')
    const liberar = servidor.retener('/api/turnos/11')

    await usuario.click(botonReprogramar())
    await usuario.click(botonReprogramar())

    expect(botonReprogramar().disabled).toBe(true)
    liberar()
    expect(await screen.findByText('Turno reprogramado.')).toBeDefined()
    expect(servidor.llamadas('PATCH', '/api/turnos/11')).toBe(1)
  })

  it('REP-7c: sin conexión se conserva lo cargado', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirReprogramar(usuario)
    cambiarCampo('Hora', '12:30')
    servidor.caerse()

    await usuario.click(botonReprogramar())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain(MENSAJE_DE_CONEXION)
    expect(aviso.textContent).toContain('El turno no cambió.')
    expect(botonReprogramar().disabled).toBe(false)
    expect(screen.queryByText('Turno reprogramado.')).toBeNull()
    expect((screen.getByLabelText('Hora') as HTMLInputElement).value).toBe('12:30')
  })

  it('REP-7c: con el refresh vigente se renueva sin aviso', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirReprogramar(usuario)
    cambiarCampo('Hora', '12:30')
    const refrescosAntes = servidor.llamadas('POST', '/api/auth/refresh')
    servidor.vencerAccess()

    await usuario.click(botonReprogramar())

    expect(await screen.findByText('Turno reprogramado.')).toBeDefined()
    expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(refrescosAntes + 1)
    expect(servidor.llamadas('PATCH', '/api/turnos/11')).toBe(2)
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('REP-7c: una sesión irrenovable vuelve al inicio de sesión', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirReprogramar(usuario)
    cambiarCampo('Hora', '12:30')
    servidor.vencerAccess()
    servidor.invalidarRefresh()

    await usuario.click(botonReprogramar())

    expect((await screen.findByRole('status')).textContent).toBe('Tu sesión terminó. Iniciá sesión de nuevo.')
    expect(screen.getByTestId('lugar').textContent).toBe('/ingresar')
    expect(screen.queryByText(MENSAJE_DE_CONEXION)).toBeNull()
    expect(servidor.turnosActuales().find((t) => t.id === 11)?.inicio).toBe('2026-11-02T12:00:00Z')
  })

  it('REP-7d: el dueño ve la acción y recibe el 403', async () => {
    const servidor = falso({ usuarios: [...USUARIOS_DE_PARTIDA, USUARIO_DUENO] })
    const usuario = await abrirAgenda(servidor, EMAIL_DUENO)
    expect(screen.getAllByRole('button', { name: /^Reprogramar el turno/ })).toHaveLength(3)
    await abrirReprogramar(usuario)
    cambiarCampo('Hora', '12:30')

    await usuario.click(botonReprogramar())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain('Tu usuario no tiene permiso para reprogramar turnos (RN-AU-05).')
    expect(aviso.textContent).toContain('El turno no cambió.')
    comprobarQueNoCambio(servidor, '12:30', '30')
  })
})
