import { cleanup, render, screen, within } from '@testing-library/react'
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
  type OpcionesDelServidorFalso,
  type ServidorFalso,
  type TurnoFalso,
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

const ANA = 'Cancelar el turno de Ana Ejemplo, 09:00'
const BRUNO = 'Cancelar el turno de Bruno Ficticio, 10:00'
const CARLA = 'Cancelar el turno de Carla Inventada, 11:00'
const MENSAJE_DE_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'

function botonDeCancelar(nombre: string): HTMLElement {
  return screen.getByRole('button', { name: nombre })
}

async function abrirCancelar(usuario: Usuario, nombre = ANA): Promise<HTMLElement> {
  await usuario.click(botonDeCancelar(nombre))
  return screen.findByRole('complementary', { name: 'Cancelar turno' })
}

function totalDePeticiones(servidor: ServidorFalso): number {
  return servidor.rutasPedidas().reduce((suma, ruta) => suma + servidor.peticiones(ruta), 0)
}

function filaDe(texto: string): HTMLElement {
  const fila = screen.getAllByRole('row').find((f) => f.textContent?.includes(texto))
  if (fila === undefined) throw new Error(`No hay una fila con «${texto}»`)
  return fila
}

function filasSeleccionadas(): string[] {
  return [...document.querySelectorAll('tr.fila-seleccionada')].map((fila) => fila.textContent ?? '')
}

function turnoExtra(id: number, hora: number, estado: string): TurnoFalso {
  const inicio = `2026-11-02T${String(hora + 3).padStart(2, '0')}:00:00Z`
  const fin = `2026-11-02T${String(hora + 3).padStart(2, '0')}:30:00Z`
  return { id, inicio, fin, estado, profesional_id: 1, sillon_id: 1, paciente_id: 2, prestacion_id: 1 }
}

beforeEach(() => {
  sessionStorage.clear()
})

afterEach(() => {
  cleanup()
})

describe('PanelCancelar: cancelar desde la agenda', () => {
  it('CAN-4a: la recepcionista cancela un turno a pedido del paciente', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    const antes = totalDePeticiones(servidor)

    const panel = await abrirCancelar(usuario)

    expect(within(panel).getByRole('heading', { name: 'Cancelar turno' })).toBeDefined()
    expect(within(panel).getByText('Ana Ejemplo · Consulta / control')).toBeDefined()
    expect(within(panel).getByText('lunes 2 de noviembre de 2026, 09:00 – 09:30 · Reservado')).toBeDefined()
    const grupo = within(panel).getByRole('group', { name: '¿Quién pidió la cancelación?' })
    const paciente = within(grupo).getByRole('radio', { name: 'El paciente' }) as HTMLInputElement
    const consultorio = within(grupo).getByRole('radio', { name: 'El consultorio' }) as HTMLInputElement
    expect([paciente.checked, consultorio.checked]).toEqual([false, false])
    expect(within(panel).getByText('El horario queda libre para otro turno.')).toBeDefined()
    expect(totalDePeticiones(servidor)).toBe(antes)
    expect(document.activeElement).toBe(paciente)
    expect(filasSeleccionadas()).toHaveLength(1)
    expect(filasSeleccionadas()[0]).toContain('Ana Ejemplo')

    await usuario.click(paciente)
    await usuario.click(within(panel).getByRole('button', { name: 'Cancelar turno' }))

    expect(await screen.findByText('Turno cancelado.')).toBeDefined()
    expect(servidor.llamadas('POST', '/api/turnos/11/cancelar')).toBe(1)
    expect(servidor.cuerpos('POST', '/api/turnos/11/cancelar')).toEqual([{ estado: 'cancelado_paciente' }])
    expect(screen.queryByRole('complementary', { name: 'Cancelar turno' })).toBeNull()
    expect(servidor.peticiones('/api/turnos?fecha=2026-11-02')).toBe(1)
    const fila = filaDe('Ana Ejemplo')
    expect(within(fila).getAllByRole('cell').slice(0, 4).map((c) => c.textContent)).toEqual([
      '09:00 – 09:30',
      'Ana Ejemplo',
      'Consulta / control',
      'Cancelado por el paciente',
    ])
    expect(within(fila).queryByRole('button', { name: /^Historial/ })).not.toBeNull()
    expect(within(fila).queryByRole('button', { name: /^Reprogramar/ })).toBeNull()
    expect(within(fila).queryByRole('button', { name: /^Cancelar/ })).toBeNull()
  })
})

function opcion(nombre: string): HTMLInputElement {
  return screen.getByRole('radio', { name: nombre }) as HTMLInputElement
}

function botonCancelarTurno(): HTMLButtonElement {
  return screen.getByRole('button', { name: 'Cancelar turno' }) as HTMLButtonElement
}

function celdasDeFila(texto: string): (string | null)[] {
  return within(filaDe(texto)).getAllByRole('cell').slice(0, 4).map((c) => c.textContent)
}

describe('PanelCancelar: bordes', () => {
  it('CAN-4b: por el consultorio manda cancelado_profesional', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor, EMAIL_ODONTOLOGA)
    await abrirCancelar(usuario, CARLA)

    await usuario.click(opcion('El consultorio'))
    await usuario.click(botonCancelarTurno())

    expect(await screen.findByText('Turno cancelado.')).toBeDefined()
    expect(servidor.cuerpos('POST', '/api/turnos/13/cancelar')).toEqual([{ estado: 'cancelado_profesional' }])
    expect(celdasDeFila('Carla Inventada')[3]).toBe('Cancelado por el consultorio')
    const fila = filaDe('Carla Inventada')
    expect(within(fila).queryByRole('button', { name: /^Reprogramar/ })).toBeNull()
    expect(within(fila).queryByRole('button', { name: /^Cancelar/ })).toBeNull()
  })

  it('CAN-4b: un pendiente_aprobacion se cancela', async () => {
    const servidor = falso({ turnos: [...TURNOS_DE_LA_AGENDA, turnoExtra(18, 13, 'pendiente_aprobacion')] })
    const usuario = await abrirAgenda(servidor)
    await abrirCancelar(usuario, 'Cancelar el turno de Bruno Ficticio, 13:00')

    await usuario.click(opcion('El paciente'))
    await usuario.click(botonCancelarTurno())

    await screen.findByText('Turno cancelado.')
    expect(servidor.cuerpos('POST', '/api/turnos/18/cancelar')).toEqual([{ estado: 'cancelado_paciente' }])
    expect(celdasDeFila('13:00 – 13:30')[3]).toBe('Cancelado por el paciente')
  })

  it('CAN-4b: un pendiente_sena se cancela', async () => {
    const servidor = falso({ turnos: [...TURNOS_DE_LA_AGENDA, turnoExtra(19, 14, 'pendiente_sena')] })
    const usuario = await abrirAgenda(servidor)
    await abrirCancelar(usuario, 'Cancelar el turno de Bruno Ficticio, 14:00')

    await usuario.click(opcion('El paciente'))
    await usuario.click(botonCancelarTurno())

    await screen.findByText('Turno cancelado.')
    expect(servidor.cuerpos('POST', '/api/turnos/19/cancelar')).toEqual([{ estado: 'cancelado_paciente' }])
    expect(celdasDeFila('14:00 – 14:30')[3]).toBe('Cancelado por el paciente')
  })

  it('CAN-4b: la recarga falla después del 200', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirCancelar(usuario, BRUNO)
    await usuario.click(opcion('El paciente'))
    servidor.fallarRuta('/api/turnos?fecha=2026-11-02', 'red')

    await usuario.click(botonCancelarTurno())

    expect(await screen.findByText('Turno cancelado.')).toBeDefined()
    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_DE_CONEXION)
    expect(screen.queryByRole('complementary', { name: 'Cancelar turno' })).toBeNull()
    expect(servidor.llamadas('POST', '/api/turnos/12/cancelar')).toBe(1)

    servidor.repararRuta('/api/turnos?fecha=2026-11-02')
    await usuario.click(screen.getByRole('button', { name: 'Reintentar' }))

    await screen.findByText('Cancelado por el paciente')
    expect(servidor.llamadas('POST', '/api/turnos/12/cancelar')).toBe(1)
    expect(servidor.peticiones('/api/turnos?fecha=2026-11-02')).toBe(2)
    expect(celdasDeFila('Bruno Ficticio')[3]).toBe('Cancelado por el paciente')
  })

  it('CAN-4c: un solo panel entre Cancelar y Reprogramar', async () => {
    const usuario = await abrirAgenda(falso())
    await abrirCancelar(usuario)

    await usuario.click(screen.getByRole('button', { name: 'Reprogramar el turno de Ana Ejemplo, 09:00' }))

    await screen.findByRole('complementary', { name: 'Reprogramar turno' })
    expect(screen.queryByRole('complementary', { name: 'Cancelar turno' })).toBeNull()
    await abrirCancelar(usuario, BRUNO)
    expect(screen.queryByRole('complementary', { name: 'Reprogramar turno' })).toBeNull()
    expect(filasSeleccionadas()).toHaveLength(1)
    expect(filasSeleccionadas()[0]).toContain('Bruno Ficticio')
  })

  it('CAN-4c: cambiar de día cierra el panel sin mandar nada', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirCancelar(usuario)
    await usuario.click(opcion('El paciente'))

    await usuario.click(screen.getByRole('button', { name: 'Día siguiente' }))

    await screen.findByText('martes 3 de noviembre de 2026')
    expect(screen.queryByRole('complementary', { name: 'Cancelar turno' })).toBeNull()
    expect(servidor.llamadas('POST', '/api/turnos/11/cancelar')).toBe(0)
  })

  it('CAN-4c: Volver devuelve el foco y no deja opción marcada', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    const antes = totalDePeticiones(servidor)
    await abrirCancelar(usuario)
    await usuario.click(opcion('El paciente'))

    await usuario.click(screen.getByRole('button', { name: 'Volver' }))

    expect(screen.queryByRole('complementary', { name: 'Cancelar turno' })).toBeNull()
    expect(document.activeElement).toBe(botonDeCancelar(ANA))
    expect(filasSeleccionadas()).toEqual([])
    expect(totalDePeticiones(servidor)).toBe(antes)
    await abrirCancelar(usuario)
    expect([opcion('El paciente').checked, opcion('El consultorio').checked]).toEqual([false, false])
  })

  it('CAN-4c: Cerrar devuelve el foco al botón de la fila', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirCancelar(usuario)

    await usuario.click(screen.getByRole('button', { name: 'Cerrar' }))

    expect(screen.queryByRole('complementary', { name: 'Cancelar turno' })).toBeNull()
    expect(document.activeElement).toBe(botonDeCancelar(ANA))
    expect(filasSeleccionadas()).toEqual([])
    expect(servidor.llamadas('POST', '/api/turnos/11/cancelar')).toBe(0)
  })

  it('CAN-4c: los turnos no activos no tienen Reprogramar ni Cancelar', async () => {
    const servidor = falso({
      turnos: [
        ...TURNOS_DE_LA_AGENDA,
        turnoExtra(14, 12, 'cancelado_paciente'),
        turnoExtra(15, 13, 'atendido'),
        turnoExtra(16, 14, 'ausente'),
        turnoExtra(17, 15, 'vencido'),
        turnoExtra(20, 18, 'cancelado_profesional'),
      ],
    })
    await abrirAgenda(servidor)

    const filas = screen.getAllByRole('row').slice(1)

    expect(filas).toHaveLength(8)
    const nombresDeBotones = filas.map((fila) => within(fila).getAllByRole('button').map((b) => b.textContent))
    expect(nombresDeBotones).toEqual([
      ['Reprogramar', 'Cancelar', 'Historial'],
      ['Reprogramar', 'Cancelar', 'Historial'],
      ['Reprogramar', 'Cancelar', 'Historial'],
      ['Historial'],
      ['Historial'],
      ['Historial'],
      ['Historial'],
      ['Historial'],
    ])
    expect(celdasDeFila('18:00 – 18:30')[3]).toBe('Cancelado por el consultorio')
  })
})

describe('PanelCancelar: los rechazos', () => {
  it('CAN-5a: un turno que ya no está activo muestra RN-AG-12 y no cambia', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirCancelar(usuario)
    servidor.cambiarEstado(11, 'cancelado_profesional')

    await usuario.click(opcion('El paciente'))
    await usuario.click(botonCancelarTurno())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain('Este turno ya no se puede cancelar por su estado (RN-AG-12).')
    expect(aviso.textContent).toContain('El turno no cambió.')
    expect(servidor.llamadas('POST', '/api/turnos/11/cancelar')).toBe(1)
    expect(screen.getByRole('complementary', { name: 'Cancelar turno' })).toBeDefined()
    expect(opcion('El paciente').checked).toBe(true)
    expect(screen.queryByText('Turno cancelado.')).toBeNull()
  })

  it('CAN-5a: el éxito de una cancelación anterior no queda junto al rechazo de la siguiente', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirCancelar(usuario)
    await usuario.click(opcion('El paciente'))
    await usuario.click(botonCancelarTurno())
    await screen.findByText('Turno cancelado.')
    await abrirCancelar(usuario, BRUNO)
    servidor.cambiarEstado(12, 'cancelado_profesional')

    await usuario.click(opcion('El paciente'))
    await usuario.click(botonCancelarTurno())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain('Este turno ya no se puede cancelar por su estado (RN-AG-12).')
    expect(screen.queryByText('Turno cancelado.')).toBeNull()
  })

  it('CAN-5b: sin opción no manda nada', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirCancelar(usuario)
    const antes = totalDePeticiones(servidor)

    await usuario.click(botonCancelarTurno())

    expect((await screen.findByRole('alert')).textContent).toContain('Elegí quién pidió la cancelación.')
    expect(totalDePeticiones(servidor)).toBe(antes)
    expect(servidor.llamadas('POST', '/api/turnos/11/cancelar')).toBe(0)
    await usuario.click(opcion('El paciente'))
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('CAN-5b: el 404 con su texto', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirCancelar(usuario)
    servidor.quitarTurno(11)

    await usuario.click(opcion('El consultorio'))
    await usuario.click(botonCancelarTurno())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain('El turno ya no existe (RN-GL-04).')
    expect(aviso.textContent).toContain('El turno no cambió.')
    expect(opcion('El consultorio').checked).toBe(true)
    expect(screen.queryByText('Turno cancelado.')).toBeNull()
  })

  it('CAN-5b: el dueño ve la acción y recibe el 403', async () => {
    const servidor = falso({ usuarios: [...USUARIOS_DE_PARTIDA, USUARIO_DUENO] })
    const usuario = await abrirAgenda(servidor, EMAIL_DUENO)
    expect(screen.getAllByRole('button', { name: /^Cancelar el turno/ })).toHaveLength(3)
    await abrirCancelar(usuario)
    const refrescosAntes = servidor.llamadas('POST', '/api/auth/refresh')

    await usuario.click(opcion('El paciente'))
    await usuario.click(botonCancelarTurno())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain('Tu usuario no tiene permiso para cancelar turnos (RN-AU-05).')
    expect(aviso.textContent).toContain('El turno no cambió.')
    expect(opcion('El paciente').checked).toBe(true)
    expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(refrescosAntes)
    expect(servidor.turnosActuales().find((t) => t.id === 11)?.estado).toBe('reservado')
  })

  it('CAN-5b: el doble clic manda un solo POST', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirCancelar(usuario)
    await usuario.click(opcion('El paciente'))
    const liberar = servidor.retener('/api/turnos/11/cancelar')

    await usuario.click(botonCancelarTurno())
    expect(botonCancelarTurno().disabled).toBe(true)
    await usuario.click(botonCancelarTurno())
    liberar()

    await screen.findByText('Turno cancelado.')
    expect(servidor.llamadas('POST', '/api/turnos/11/cancelar')).toBe(1)
  })

  it('CAN-5b: sin conexión se conserva la opción', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirCancelar(usuario)
    await usuario.click(opcion('El consultorio'))
    servidor.caerse()

    await usuario.click(botonCancelarTurno())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain(MENSAJE_DE_CONEXION)
    expect(aviso.textContent).toContain('El turno no cambió.')
    expect(botonCancelarTurno().disabled).toBe(false)
    expect(opcion('El consultorio').checked).toBe(true)
    expect(screen.queryByText('Turno cancelado.')).toBeNull()
  })

  it('CAN-5b: un 500 muestra el aviso de conexión', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirCancelar(usuario)
    await usuario.click(opcion('El paciente'))
    servidor.responderAlCancelar(500, [])

    await usuario.click(botonCancelarTurno())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain(MENSAJE_DE_CONEXION)
    expect(aviso.textContent).toContain('El turno no cambió.')
    expect(opcion('El paciente').checked).toBe(true)
    expect(screen.queryByText('Turno cancelado.')).toBeNull()
  })

  it('CAN-5b: un 422 muestra el aviso de conexión', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirCancelar(usuario)
    await usuario.click(opcion('El consultorio'))
    servidor.responderAlCancelar(422, [])

    await usuario.click(botonCancelarTurno())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain(MENSAJE_DE_CONEXION)
    expect(aviso.textContent).toContain('El turno no cambió.')
    expect(opcion('El consultorio').checked).toBe(true)
    expect(screen.queryByText('Turno cancelado.')).toBeNull()
  })

  it('CAN-5b: con el refresh vigente se renueva sin aviso', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirCancelar(usuario)
    await usuario.click(opcion('El paciente'))
    const refrescosAntes = servidor.llamadas('POST', '/api/auth/refresh')
    servidor.vencerAccess()

    await usuario.click(botonCancelarTurno())

    expect(await screen.findByText('Turno cancelado.')).toBeDefined()
    expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(refrescosAntes + 1)
    expect(servidor.llamadas('POST', '/api/turnos/11/cancelar')).toBe(2)
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('CAN-5b: una sesión irrenovable vuelve al inicio de sesión', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirCancelar(usuario)
    await usuario.click(opcion('El paciente'))
    servidor.vencerAccess()
    servidor.invalidarRefresh()

    await usuario.click(botonCancelarTurno())

    expect((await screen.findByRole('status')).textContent).toBe('Tu sesión terminó. Iniciá sesión de nuevo.')
    expect(screen.getByTestId('lugar').textContent).toBe('/ingresar')
    expect(screen.queryByText(MENSAJE_DE_CONEXION)).toBeNull()
    expect(servidor.turnosActuales().find((t) => t.id === 11)?.estado).toBe('reservado')
  })
})
