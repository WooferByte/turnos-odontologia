import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { App } from '../../App'
import { CLAVE_DE_SESION } from '../../shared/api/sesion'
import {
  EMAIL_ACTIVA as EMAIL_ODONTOLOGA,
  EMAIL_RECEPCIONISTA,
  PRESTACIONES_DE_PARTIDA,
  TURNOS_DE_LA_AGENDA,
  crearServidorFalso,
  type TurnoFalso,
  type OpcionesDelServidorFalso,
  type ServidorFalso,
} from '../../test/servidorFalso'

type Usuario = ReturnType<typeof userEvent.setup>

/** El falso con las prestaciones de la demo y los tres turnos del 2 de noviembre. */
function falso(opciones: OpcionesDelServidorFalso = {}): ServidorFalso {
  return crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA, turnos: TURNOS_DE_LA_AGENDA, ...opciones })
}

/** Monta la aplicación con una sesión guardada y espera la agenda del 2 de noviembre. */
async function abrirAgenda(servidor: ServidorFalso, email = EMAIL_RECEPCIONISTA): Promise<Usuario> {
  sessionStorage.setItem(CLAVE_DE_SESION, JSON.stringify({ refresh: servidor.emitirSesion(email).refresh }))
  render(
    <MemoryRouter initialEntries={['/panel/agenda']}>
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
