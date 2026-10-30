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

const ANA = 'Registrar la asistencia del turno de Ana Ejemplo, 09:00'
const BRUNO = 'Registrar la asistencia del turno de Bruno Ficticio, 10:00'
const CARLA = 'Registrar la asistencia del turno de Carla Inventada, 11:00'
const MENSAJE_DE_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'

function botonDeAsistencia(nombre: string): HTMLElement {
  return screen.getByRole('button', { name: nombre })
}

async function abrirAsistencia(usuario: Usuario, nombre = ANA): Promise<HTMLElement> {
  await usuario.click(botonDeAsistencia(nombre))
  return screen.findByRole('complementary', { name: 'Registrar asistencia' })
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

function opcion(nombre: string): HTMLInputElement {
  return screen.getByRole('radio', { name: nombre }) as HTMLInputElement
}

function botonRegistrar(): HTMLButtonElement {
  return screen.getByRole('button', { name: 'Registrar asistencia' }) as HTMLButtonElement
}

function celdasDeFila(texto: string): (string | null)[] {
  return within(filaDe(texto)).getAllByRole('cell').slice(0, 4).map((c) => c.textContent)
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

describe('PanelAsistencia: registrar la asistencia desde la agenda', () => {
  it('ASI-5a: la recepcionista registra que el paciente fue atendido', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    const antes = totalDePeticiones(servidor)

    const panel = await abrirAsistencia(usuario)

    expect(within(panel).getByRole('heading', { name: 'Registrar asistencia' })).toBeDefined()
    expect(within(panel).getByText('Ana Ejemplo · Consulta / control')).toBeDefined()
    expect(within(panel).getByText('lunes 2 de noviembre de 2026, 09:00 – 09:30 · Reservado')).toBeDefined()
    const grupo = within(panel).getByRole('group', { name: '¿Cómo terminó el turno?' })
    const atendido = within(grupo).getByRole('radio', { name: 'Atendido' }) as HTMLInputElement
    const ausente = within(grupo).getByRole('radio', { name: 'Ausente' }) as HTMLInputElement
    expect([atendido.checked, ausente.checked]).toEqual([false, false])
    expect(within(panel).getByText('El horario queda libre para otro turno.')).toBeDefined()
    expect(totalDePeticiones(servidor)).toBe(antes)
    expect(document.activeElement).toBe(atendido)
    expect(filasSeleccionadas()).toHaveLength(1)
    expect(filasSeleccionadas()[0]).toContain('Ana Ejemplo')

    await usuario.click(atendido)
    await usuario.click(within(panel).getByRole('button', { name: 'Registrar asistencia' }))

    expect(await screen.findByText('Asistencia registrada.')).toBeDefined()
    expect(servidor.llamadas('POST', '/api/turnos/11/estado')).toBe(1)
    expect(servidor.cuerpos('POST', '/api/turnos/11/estado')).toEqual([{ estado: 'atendido' }])
    expect(screen.queryByRole('complementary', { name: 'Registrar asistencia' })).toBeNull()
    expect(servidor.peticiones('/api/turnos?fecha=2026-11-02')).toBe(1)
    const fila = filaDe('Ana Ejemplo')
    expect(within(fila).getAllByRole('cell').slice(0, 4).map((c) => c.textContent)).toEqual([
      '09:00 – 09:30',
      'Ana Ejemplo',
      'Consulta / control',
      'Atendido',
    ])
    expect(within(fila).queryByRole('button', { name: /^Historial/ })).not.toBeNull()
    expect(within(fila).queryByRole('button', { name: /^Registrar la asistencia/ })).toBeNull()
    expect(within(fila).queryByRole('button', { name: /^Reprogramar/ })).toBeNull()
    expect(within(fila).queryByRole('button', { name: /^Cancelar/ })).toBeNull()
  })
})

describe('PanelAsistencia: bordes', () => {
  it('ASI-5b: ausente en un turno confirmado', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor, EMAIL_ODONTOLOGA)
    await abrirAsistencia(usuario, CARLA)

    await usuario.click(opcion('Ausente'))
    await usuario.click(botonRegistrar())

    expect(await screen.findByText('Asistencia registrada.')).toBeDefined()
    expect(servidor.cuerpos('POST', '/api/turnos/13/estado')).toEqual([{ estado: 'ausente' }])
    expect(celdasDeFila('Carla Inventada')[3]).toBe('Ausente')
    const fila = filaDe('Carla Inventada')
    expect(within(fila).queryByRole('button', { name: /^Registrar la asistencia/ })).toBeNull()
    expect(within(fila).queryByRole('button', { name: /^Reprogramar/ })).toBeNull()
    expect(within(fila).queryByRole('button', { name: /^Cancelar/ })).toBeNull()
  })

  it('ASI-5b: la recarga falla después del 200', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirAsistencia(usuario, BRUNO)
    await usuario.click(opcion('Atendido'))
    servidor.fallarRuta('/api/turnos?fecha=2026-11-02', 'red')

    await usuario.click(botonRegistrar())

    expect(await screen.findByText('Asistencia registrada.')).toBeDefined()
    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_DE_CONEXION)
    expect(screen.queryByRole('complementary', { name: 'Registrar asistencia' })).toBeNull()
    expect(servidor.llamadas('POST', '/api/turnos/12/estado')).toBe(1)

    servidor.repararRuta('/api/turnos?fecha=2026-11-02')
    await usuario.click(screen.getByRole('button', { name: 'Reintentar' }))

    await screen.findByText('Atendido')
    expect(servidor.llamadas('POST', '/api/turnos/12/estado')).toBe(1)
    expect(servidor.peticiones('/api/turnos?fecha=2026-11-02')).toBe(2)
    expect(celdasDeFila('Bruno Ficticio')[3]).toBe('Atendido')
  })

  it('ASI-5c: un solo panel entre Asistencia y Cancelar', async () => {
    const usuario = await abrirAgenda(falso())
    await abrirAsistencia(usuario)

    await usuario.click(screen.getByRole('button', { name: 'Cancelar el turno de Ana Ejemplo, 09:00' }))

    await screen.findByRole('complementary', { name: 'Cancelar turno' })
    expect(screen.queryByRole('complementary', { name: 'Registrar asistencia' })).toBeNull()
    await abrirAsistencia(usuario)
    expect(screen.queryByRole('complementary', { name: 'Cancelar turno' })).toBeNull()
    expect(filasSeleccionadas()).toHaveLength(1)
  })

  it('ASI-5c: cambiar de día cierra el panel sin mandar nada', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirAsistencia(usuario)
    await usuario.click(opcion('Atendido'))

    await usuario.click(screen.getByRole('button', { name: 'Día siguiente' }))

    await screen.findByText('martes 3 de noviembre de 2026')
    expect(screen.queryByRole('complementary', { name: 'Registrar asistencia' })).toBeNull()
    expect(servidor.llamadas('POST', '/api/turnos/11/estado')).toBe(0)
  })

  it('ASI-5c: Volver devuelve el foco y no deja opción marcada', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    const antes = totalDePeticiones(servidor)
    await abrirAsistencia(usuario)
    await usuario.click(opcion('Ausente'))

    await usuario.click(screen.getByRole('button', { name: 'Volver' }))

    expect(screen.queryByRole('complementary', { name: 'Registrar asistencia' })).toBeNull()
    expect(document.activeElement).toBe(botonDeAsistencia(ANA))
    expect(filasSeleccionadas()).toEqual([])
    expect(totalDePeticiones(servidor)).toBe(antes)
    await abrirAsistencia(usuario)
    expect([opcion('Atendido').checked, opcion('Ausente').checked]).toEqual([false, false])
  })

  it('ASI-5c: Cerrar devuelve el foco al botón de la fila', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirAsistencia(usuario)

    await usuario.click(screen.getByRole('button', { name: 'Cerrar' }))

    expect(screen.queryByRole('complementary', { name: 'Registrar asistencia' })).toBeNull()
    expect(document.activeElement).toBe(botonDeAsistencia(ANA))
    expect(filasSeleccionadas()).toEqual([])
    expect(servidor.llamadas('POST', '/api/turnos/11/estado')).toBe(0)
  })

  it('ASI-5c: solo reservado y confirmado tienen Asistencia', async () => {
    const servidor = falso({
      turnos: [
        ...TURNOS_DE_LA_AGENDA,
        turnoExtra(14, 12, 'cancelado_paciente'),
        turnoExtra(15, 13, 'atendido'),
        turnoExtra(16, 14, 'ausente'),
        turnoExtra(17, 15, 'vencido'),
        turnoExtra(18, 16, 'pendiente_aprobacion'),
        turnoExtra(19, 17, 'pendiente_sena'),
        turnoExtra(20, 18, 'cancelado_profesional'),
      ],
    })
    await abrirAgenda(servidor)

    const filas = screen.getAllByRole('row').slice(1)

    expect(filas).toHaveLength(10)
    const nombresDeBotones = filas.map((fila) => within(fila).getAllByRole('button').map((b) => b.textContent))
    expect(nombresDeBotones).toEqual([
      ['Asistencia', 'Reprogramar', 'Cancelar', 'Historial'],
      ['Asistencia', 'Reprogramar', 'Cancelar', 'Historial'],
      ['Asistencia', 'Reprogramar', 'Cancelar', 'Historial'],
      ['Historial'],
      ['Historial'],
      ['Historial'],
      ['Historial'],
      ['Reprogramar', 'Cancelar', 'Historial'],
      ['Reprogramar', 'Cancelar', 'Historial'],
      ['Historial'],
    ])
  })
})

describe('PanelAsistencia: los rechazos', () => {
  it('ASI-6a: un turno que ya no está reservado ni confirmado muestra RN-AG-12 y no cambia', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirAsistencia(usuario)
    servidor.cambiarEstado(11, 'atendido')

    await usuario.click(opcion('Ausente'))
    await usuario.click(botonRegistrar())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain('Este turno ya no admite registrar la asistencia por su estado (RN-AG-12).')
    expect(aviso.textContent).toContain('El turno no cambió.')
    expect(servidor.llamadas('POST', '/api/turnos/11/estado')).toBe(1)
    expect(screen.getByRole('complementary', { name: 'Registrar asistencia' })).toBeDefined()
    expect(opcion('Ausente').checked).toBe(true)
    expect(screen.queryByText('Asistencia registrada.')).toBeNull()
  })
  it('ASI-6a: el éxito de un registro anterior no queda junto al rechazo del siguiente', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirAsistencia(usuario)
    await usuario.click(opcion('Atendido'))
    await usuario.click(botonRegistrar())
    await screen.findByText('Asistencia registrada.')
    await abrirAsistencia(usuario, BRUNO)
    servidor.cambiarEstado(12, 'ausente')

    await usuario.click(opcion('Atendido'))
    await usuario.click(botonRegistrar())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain('Este turno ya no admite registrar la asistencia por su estado (RN-AG-12).')
    expect(screen.queryByText('Asistencia registrada.')).toBeNull()
  })

  it('ASI-6b: un turno que todavía no empezó muestra RN-AG-13', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirAsistencia(usuario, CARLA)
    servidor.responderAlMarcar(409, ['RN-AG-13'])

    await usuario.click(opcion('Atendido'))
    await usuario.click(botonRegistrar())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain(
      'El turno todavía no empezó: la asistencia se registra desde su hora de inicio (RN-AG-13).',
    )
    expect(aviso.textContent).toContain('El turno no cambió.')
    expect(servidor.llamadas('POST', '/api/turnos/13/estado')).toBe(1)
    expect(screen.getByRole('complementary', { name: 'Registrar asistencia' })).toBeDefined()
    expect(opcion('Atendido').checked).toBe(true)
    expect(screen.queryByText('Asistencia registrada.')).toBeNull()
  })

  it('ASI-6c: sin opción no manda nada', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirAsistencia(usuario)
    const antes = totalDePeticiones(servidor)

    await usuario.click(botonRegistrar())

    expect((await screen.findByRole('alert')).textContent).toContain(
      'Elegí si el paciente fue atendido o estuvo ausente.',
    )
    expect(totalDePeticiones(servidor)).toBe(antes)
    expect(servidor.llamadas('POST', '/api/turnos/11/estado')).toBe(0)
    await usuario.click(opcion('Atendido'))
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('ASI-6c: el 404 con su texto', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirAsistencia(usuario)
    servidor.quitarTurno(11)

    await usuario.click(opcion('Ausente'))
    await usuario.click(botonRegistrar())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain('El turno ya no existe (RN-GL-04).')
    expect(aviso.textContent).toContain('El turno no cambió.')
    expect(opcion('Ausente').checked).toBe(true)
    expect(screen.queryByText('Asistencia registrada.')).toBeNull()
  })

  it('ASI-6c: el dueño ve la acción y recibe el 403', async () => {
    const servidor = falso({ usuarios: [...USUARIOS_DE_PARTIDA, USUARIO_DUENO] })
    const usuario = await abrirAgenda(servidor, EMAIL_DUENO)
    expect(screen.getAllByRole('button', { name: /^Registrar la asistencia del turno/ })).toHaveLength(3)
    await abrirAsistencia(usuario)
    const refrescosAntes = servidor.llamadas('POST', '/api/auth/refresh')

    await usuario.click(opcion('Atendido'))
    await usuario.click(botonRegistrar())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain('Tu usuario no tiene permiso para registrar la asistencia (RN-AU-05).')
    expect(aviso.textContent).toContain('El turno no cambió.')
    expect(opcion('Atendido').checked).toBe(true)
    expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(refrescosAntes)
    expect(servidor.turnosActuales().find((t) => t.id === 11)?.estado).toBe('reservado')
  })

  it('ASI-6c: el doble clic manda un solo POST', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirAsistencia(usuario)
    await usuario.click(opcion('Atendido'))
    const liberar = servidor.retener('/api/turnos/11/estado')

    await usuario.click(botonRegistrar())
    expect(botonRegistrar().disabled).toBe(true)
    await usuario.click(botonRegistrar())
    liberar()

    await screen.findByText('Asistencia registrada.')
    expect(servidor.llamadas('POST', '/api/turnos/11/estado')).toBe(1)
  })

  it('ASI-6c: sin conexión se conserva la opción', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirAsistencia(usuario)
    await usuario.click(opcion('Ausente'))
    servidor.caerse()

    await usuario.click(botonRegistrar())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain(MENSAJE_DE_CONEXION)
    expect(aviso.textContent).toContain('El turno no cambió.')
    expect(botonRegistrar().disabled).toBe(false)
    expect(opcion('Ausente').checked).toBe(true)
    expect(screen.queryByText('Asistencia registrada.')).toBeNull()
  })

  it('ASI-6c: un 500 muestra el aviso de conexión', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirAsistencia(usuario)
    await usuario.click(opcion('Atendido'))
    servidor.responderAlMarcar(500, [])

    await usuario.click(botonRegistrar())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain(MENSAJE_DE_CONEXION)
    expect(aviso.textContent).toContain('El turno no cambió.')
    expect(opcion('Atendido').checked).toBe(true)
    expect(screen.queryByText('Asistencia registrada.')).toBeNull()
  })

  it('ASI-6c: un 422 muestra el aviso de conexión', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirAsistencia(usuario)
    await usuario.click(opcion('Ausente'))
    servidor.responderAlMarcar(422, [])

    await usuario.click(botonRegistrar())

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain(MENSAJE_DE_CONEXION)
    expect(aviso.textContent).toContain('El turno no cambió.')
    expect(opcion('Ausente').checked).toBe(true)
    expect(screen.queryByText('Asistencia registrada.')).toBeNull()
  })

  it('ASI-6c: con el refresh vigente se renueva sin aviso', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirAsistencia(usuario)
    await usuario.click(opcion('Atendido'))
    const refrescosAntes = servidor.llamadas('POST', '/api/auth/refresh')
    servidor.vencerAccess()

    await usuario.click(botonRegistrar())

    expect(await screen.findByText('Asistencia registrada.')).toBeDefined()
    expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(refrescosAntes + 1)
    expect(servidor.llamadas('POST', '/api/turnos/11/estado')).toBe(2)
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('ASI-6c: una sesión irrenovable vuelve al inicio de sesión', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await abrirAsistencia(usuario)
    await usuario.click(opcion('Atendido'))
    servidor.vencerAccess()
    servidor.invalidarRefresh()

    await usuario.click(botonRegistrar())

    expect((await screen.findByRole('status')).textContent).toBe('Tu sesión terminó. Iniciá sesión de nuevo.')
    expect(screen.getByTestId('lugar').textContent).toBe('/ingresar')
    expect(screen.queryByText(MENSAJE_DE_CONEXION)).toBeNull()
    expect(servidor.turnosActuales().find((t) => t.id === 11)?.estado).toBe('reservado')
  })
})
