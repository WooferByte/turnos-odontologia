import { cleanup, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { App } from '../../App'
import { CLAVE_DE_SESION } from '../../shared/api/sesion'
import {
  EMAIL_ACTIVA,
  EMAIL_DUENO,
  EMAIL_RECEPCIONISTA,
  EVENTO_CREADO_DEL_TURNO_11,
  PRESTACIONES_DE_PARTIDA,
  TURNOS_DE_LA_AGENDA,
  USUARIOS_DE_PARTIDA,
  USUARIO_DUENO,
  crearServidorFalso,
  type OpcionesDelServidorFalso,
  type ServidorFalso,
} from '../../test/servidorFalso'

type Usuario = ReturnType<typeof userEvent.setup>

const MENSAJE_DE_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'

function LugarActual() {
  const ubicacion = useLocation()
  return <p data-testid="lugar">{ubicacion.pathname}</p>
}

const HISTORIAL_DEL_TURNO_11 = { 11: [EVENTO_CREADO_DEL_TURNO_11] }

/** El falso con las prestaciones y los tres turnos del 2 de noviembre y el historial del turno 11 (HIS-2a). */
function falso(opciones: OpcionesDelServidorFalso = {}): ServidorFalso {
  return crearServidorFalso({
    prestaciones: PRESTACIONES_DE_PARTIDA,
    turnos: TURNOS_DE_LA_AGENDA,
    historiales: HISTORIAL_DEL_TURNO_11,
    ...opciones,
  })
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

function botonDeHistorial(nombre: string): HTMLElement {
  return screen.getByRole('button', { name: nombre })
}

const ANA = 'Historial del turno de Ana Ejemplo, 09:00'
const BRUNO = 'Historial del turno de Bruno Ficticio, 10:00'

function peticionesDeHistorial(servidor: ServidorFalso): string[] {
  return servidor.rutasPedidas().filter((ruta) => ruta.endsWith('/historial'))
}

beforeEach(() => {
  sessionStorage.clear()
})

afterEach(() => {
  cleanup()
})

describe('PanelHistorial: ver el historial desde la agenda', () => {
  it('HIS-2a: la recepcionista ve el evento creado del turno', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)

    await usuario.click(botonDeHistorial(ANA))

    const panel = await screen.findByRole('complementary', { name: 'Historial del turno' })
    await within(panel).findByText('Turno creado')
    expect(peticionesDeHistorial(servidor)).toEqual(['/api/turnos/11/historial'])
    expect(servidor.peticiones('/api/turnos/11/historial')).toBe(1)
    expect(within(panel).getByText('Ana Ejemplo · Consulta / control')).toBeDefined()
    expect(within(panel).getByText('lunes 2 de noviembre de 2026, 09:00 – 09:30')).toBeDefined()
    expect(within(panel).getByText('Solo lectura: el historial no se puede editar.')).toBeDefined()
    expect(within(panel).getByText('lunes 26 de octubre de 2026, 10:15')).toBeDefined()
    expect(within(panel).getByText('Por: Usuario n.º 2')).toBeDefined()
    expect(within(panel).getByText('Estado inicial: Reservado · 09:00 – 09:30')).toBeDefined()
    expect(within(panel).queryAllByRole('textbox')).toHaveLength(0)
    expect(within(panel).getAllByRole('button').map((b) => b.getAttribute('aria-label') ?? b.textContent)).toSatisfy(
      (nombres: string[]) => nombres.length > 0 && nombres.every((n) => n === 'Cerrar'),
    )
  })

  it.each([
    ['la odontóloga', EMAIL_ACTIVA],
    ['el dueño', EMAIL_DUENO],
  ])('HIS-2a: %s ve el historial', async (_rol, email) => {
    const usuario = await abrirAgenda(falso({ usuarios: [...USUARIOS_DE_PARTIDA, USUARIO_DUENO] }), email)

    await usuario.click(botonDeHistorial(ANA))

    const panel = await screen.findByRole('complementary', { name: 'Historial del turno' })
    await within(panel).findByText('Turno creado')
    expect(within(panel).getByText('Por: Usuario n.º 2')).toBeDefined()
  })

  it('HIS-2b: cuatro eventos en el orden de la respuesta con su actor y su fecha', async () => {
    const base = { turno_id: 12, actor_tipo: 'usuario', antes: null, despues: null }
    const servidor = falso({
      historiales: {
        12: [
          {
            ...base,
            id: 21,
            tipo: 'creado',
            actor_id: null,
            ocurrido_en: '2026-10-27T11:40:00Z',
            motivo: null,
            despues: { estado: 'reservado', inicio: '2026-11-02T13:00:00Z', fin: '2026-11-02T13:45:00Z' },
          },
          {
            ...base,
            id: 22,
            tipo: 'reprogramado',
            actor_id: '1',
            ocurrido_en: '2026-10-30T19:05:00Z',
            motivo: null,
            antes: { inicio: '2026-11-02T13:00:00Z', fin: '2026-11-02T13:45:00Z', duracion_minutos: 45 },
            despues: { inicio: '2026-11-02T13:30:00Z', fin: '2026-11-02T14:15:00Z', duracion_minutos: 45 },
          },
          {
            ...base,
            id: 23,
            tipo: 'confirmado',
            actor_id: '2',
            ocurrido_en: '2026-11-01T02:30:00Z',
            motivo: 'Pedido del paciente',
          },
          {
            ...base,
            id: 24,
            tipo: 'cancelado',
            actor_id: '2',
            ocurrido_en: '2026-11-01T14:20:00Z',
            motivo: null,
            antes: { estado: 'confirmado' },
            despues: { estado: 'cancelado_paciente' },
          },
        ],
      },
    })
    const usuario = await abrirAgenda(servidor, EMAIL_ACTIVA)

    await usuario.click(botonDeHistorial(BRUNO))

    const panel = await screen.findByRole('complementary', { name: 'Historial del turno' })
    const entradas = await within(panel).findAllByRole('listitem')
    expect(entradas.map((e) => e.textContent)).toEqual([
      'Turno creadomartes 27 de octubre de 2026, 08:40Por: Usuario del panel (sin identificar)Estado inicial: Reservado · 10:00 – 10:45',
      'Turno reprogramadoviernes 30 de octubre de 2026, 16:05Por: Usuario n.º 1Antes: lunes 2 de noviembre de 2026, 10:00 – 10:45 (45 min)Después: lunes 2 de noviembre de 2026, 10:30 – 11:15 (45 min)',
      'Cambio registrado (confirmado)sábado 31 de octubre de 2026, 23:30Por: Usuario n.º 2Motivo: Pedido del paciente',
      'Turno canceladodomingo 1 de noviembre de 2026, 11:20Por: Usuario n.º 2Estado: Confirmado → Cancelado por el paciente',
    ])
  })

  it('HIS-2b: un estado_cambiado de atendido', async () => {
    const servidor = falso({
      historiales: {
        11: [
          EVENTO_CREADO_DEL_TURNO_11,
          {
            id: 31,
            turno_id: 11,
            tipo: 'estado_cambiado',
            actor_tipo: 'usuario',
            actor_id: '2',
            ocurrido_en: '2026-11-02T13:10:00Z',
            motivo: null,
            antes: { estado: 'reservado' },
            despues: { estado: 'atendido' },
          },
        ],
      },
    })
    const usuario = await abrirAgenda(servidor, EMAIL_ACTIVA)

    await usuario.click(botonDeHistorial(ANA))

    const panel = await screen.findByRole('complementary', { name: 'Historial del turno' })
    const entradas = await within(panel).findAllByRole('listitem')
    expect(entradas.map((e) => e.textContent)).toEqual([
      'Turno creadolunes 26 de octubre de 2026, 10:15Por: Usuario n.º 2Estado inicial: Reservado · 09:00 – 09:30',
      'Cambio de estadolunes 2 de noviembre de 2026, 10:10Por: Usuario n.º 2Estado: Reservado → Atendido',
    ])
  })

  it('HIS-2b: un estado_cambiado de confirmado a ausente', async () => {
    const servidor = falso({
      historiales: {
        13: [
          {
            id: 41,
            turno_id: 13,
            tipo: 'estado_cambiado',
            actor_tipo: 'usuario',
            actor_id: '1',
            ocurrido_en: '2026-11-02T15:30:00Z',
            motivo: null,
            antes: { estado: 'confirmado' },
            despues: { estado: 'ausente' },
          },
        ],
      },
    })
    const usuario = await abrirAgenda(servidor, EMAIL_ACTIVA)

    await usuario.click(botonDeHistorial('Historial del turno de Carla Inventada, 11:00'))

    const panel = await screen.findByRole('complementary', { name: 'Historial del turno' })
    const entradas = await within(panel).findAllByRole('listitem')
    expect(entradas.map((e) => e.textContent)).toEqual([
      'Cambio de estadolunes 2 de noviembre de 2026, 12:30Por: Usuario n.º 1Estado: Confirmado → Ausente',
    ])
  })

  it('HIS-2b: un estado_cambiado sin estado en despues no tiene la línea Estado', async () => {
    const servidor = falso({
      historiales: {
        12: [
          {
            id: 42,
            turno_id: 12,
            tipo: 'estado_cambiado',
            actor_tipo: 'usuario',
            actor_id: '2',
            ocurrido_en: '2026-11-02T14:00:00Z',
            motivo: null,
            antes: { estado: 'reservado' },
            despues: {},
          },
        ],
      },
    })
    const usuario = await abrirAgenda(servidor, EMAIL_ACTIVA)

    await usuario.click(botonDeHistorial(BRUNO))

    const panel = await screen.findByRole('complementary', { name: 'Historial del turno' })
    const entradas = await within(panel).findAllByRole('listitem')
    expect(entradas.map((e) => e.textContent)).toEqual([
      'Cambio de estadolunes 2 de noviembre de 2026, 11:00Por: Usuario n.º 2',
    ])
  })

  it('HIS-2f: abrir Historial cierra Nuevo turno y al revés', async () => {
    const usuario = await abrirAgenda(falso())
    await usuario.click(screen.getByRole('button', { name: 'Nuevo turno' }))
    await screen.findByRole('complementary', { name: 'Nuevo turno' })

    await usuario.click(botonDeHistorial(ANA))

    await screen.findByRole('complementary', { name: 'Historial del turno' })
    expect(screen.queryByRole('complementary', { name: 'Nuevo turno' })).toBeNull()

    await usuario.click(screen.getByRole('button', { name: 'Nuevo turno' }))

    await screen.findByRole('complementary', { name: 'Nuevo turno' })
    expect(screen.queryByRole('complementary', { name: 'Historial del turno' })).toBeNull()
  })

  it('HIS-2f: Reprogramar e Historial, un solo panel', async () => {
    const usuario = await abrirAgenda(falso())
    await usuario.click(screen.getByRole('button', { name: 'Reprogramar el turno de Ana Ejemplo, 09:00' }))
    await screen.findByRole('complementary', { name: 'Reprogramar turno' })

    await usuario.click(botonDeHistorial(ANA))

    await screen.findByRole('complementary', { name: 'Historial del turno' })
    expect(screen.queryByRole('complementary', { name: 'Reprogramar turno' })).toBeNull()

    await usuario.click(screen.getByRole('button', { name: 'Reprogramar el turno de Bruno Ficticio, 10:00' }))

    await screen.findByRole('complementary', { name: 'Reprogramar turno' })
    expect(screen.queryByRole('complementary', { name: 'Historial del turno' })).toBeNull()
  })

  it('HIS-2f: Cancelar e Historial, un solo panel', async () => {
    const usuario = await abrirAgenda(falso())
    await usuario.click(screen.getByRole('button', { name: 'Cancelar el turno de Ana Ejemplo, 09:00' }))
    await screen.findByRole('complementary', { name: 'Cancelar turno' })

    await usuario.click(botonDeHistorial(ANA))

    await screen.findByRole('complementary', { name: 'Historial del turno' })
    expect(screen.queryByRole('complementary', { name: 'Cancelar turno' })).toBeNull()

    await usuario.click(screen.getByRole('button', { name: 'Cancelar el turno de Bruno Ficticio, 10:00' }))

    const panelDeCancelar = await screen.findByRole('complementary', { name: 'Cancelar turno' })
    expect(within(panelDeCancelar).getByText('Bruno Ficticio · Limpieza')).toBeDefined()
    expect(screen.queryByRole('complementary', { name: 'Historial del turno' })).toBeNull()
  })

  it('HIS-2f: Registrar asistencia e Historial, un solo panel', async () => {
    const usuario = await abrirAgenda(falso())
    await usuario.click(screen.getByRole('button', { name: 'Registrar la asistencia del turno de Ana Ejemplo, 09:00' }))
    await screen.findByRole('complementary', { name: 'Registrar asistencia' })

    await usuario.click(botonDeHistorial(ANA))

    await screen.findByRole('complementary', { name: 'Historial del turno' })
    expect(screen.queryByRole('complementary', { name: 'Registrar asistencia' })).toBeNull()

    await usuario.click(screen.getByRole('button', { name: 'Registrar la asistencia del turno de Bruno Ficticio, 10:00' }))

    const panelDeAsistencia = await screen.findByRole('complementary', { name: 'Registrar asistencia' })
    expect(within(panelDeAsistencia).getByText('Bruno Ficticio · Limpieza')).toBeDefined()
    expect(screen.queryByRole('complementary', { name: 'Historial del turno' })).toBeNull()
  })

  it('HIS-2f: cambiar de día cierra el historial', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await usuario.click(botonDeHistorial(ANA))
    await screen.findByText('Turno creado')

    await usuario.click(screen.getByRole('button', { name: 'Día siguiente' }))

    await screen.findByText('martes 3 de noviembre de 2026')
    expect(screen.queryByRole('complementary', { name: 'Historial del turno' })).toBeNull()
    expect(peticionesDeHistorial(servidor)).toEqual(['/api/turnos/11/historial'])
    expect(servidor.peticiones('/api/turnos/11/historial')).toBe(1)
  })
})

function tituloDelPanel(): HTMLElement {
  return screen.getByRole('heading', { name: 'Historial del turno' })
}

function botonCerrarDelPanel(): HTMLElement {
  const panel = screen.getByRole('complementary', { name: 'Historial del turno' })
  // El panel tiene dos «Cerrar» (la X de arriba y el botón del pie): se usa el del pie.
  return within(panel).getAllByRole('button', { name: 'Cerrar' }).at(-1) as HTMLElement
}

describe('PanelHistorial: vacío, cierre, foco, rechazos, carga y sesión', () => {
  it('HIS-2a: al abrir, el foco va al título del panel', async () => {
    const usuario = await abrirAgenda(falso())

    await usuario.click(botonDeHistorial(ANA))

    await screen.findByText('Turno creado')
    expect(document.activeElement).toBe(tituloDelPanel())
  })

  it('HIS-2c: un turno sin eventos', async () => {
    const usuario = await abrirAgenda(falso())

    await usuario.click(botonDeHistorial(BRUNO))

    expect(await screen.findByText('Este turno no tiene eventos registrados.')).toBeDefined()
    expect(screen.queryByText('Turno creado')).toBeNull()
  })

  it('HIS-2c: Cerrar no hace ninguna petición nueva y devuelve el foco al botón de la fila', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    await usuario.click(botonDeHistorial(BRUNO))
    await screen.findByText('Este turno no tiene eventos registrados.')

    await usuario.click(botonCerrarDelPanel())

    expect(screen.queryByRole('complementary', { name: 'Historial del turno' })).toBeNull()
    expect(screen.getByRole('table', { name: 'Turnos del día' })).toBeDefined()
    expect(document.activeElement).toBe(botonDeHistorial(BRUNO))
    expect(peticionesDeHistorial(servidor)).toEqual(['/api/turnos/12/historial'])
    expect(servidor.peticiones('/api/turnos/12/historial')).toBe(1)
  })

  it('HIS-2c: una respuesta que llega después de Cerrar no reabre el panel', async () => {
    const servidor = falso()
    const liberar = servidor.retener('/api/turnos/12/historial')
    const usuario = await abrirAgenda(servidor)
    await usuario.click(botonDeHistorial(BRUNO))
    await screen.findByText('Cargando historial…')

    await usuario.click(botonCerrarDelPanel())
    liberar()

    await waitFor(() => expect(screen.queryByRole('complementary', { name: 'Historial del turno' })).toBeNull())
    await new Promise((resolver) => setTimeout(resolver, 50))
    expect(screen.queryByRole('complementary', { name: 'Historial del turno' })).toBeNull()
    expect(screen.queryByText('Este turno no tiene eventos registrados.')).toBeNull()
  })

  it('HIS-2f: cambiar de turno muestra solo el último pedido', async () => {
    const servidor = falso()
    const liberar = servidor.retener('/api/turnos/12/historial')
    const usuario = await abrirAgenda(servidor)
    await usuario.click(botonDeHistorial(BRUNO))
    await screen.findByText('Cargando historial…')

    await usuario.click(botonDeHistorial(ANA))
    await screen.findByText('Turno creado')
    liberar()
    await new Promise((resolver) => setTimeout(resolver, 50))

    expect(screen.queryByText('Este turno no tiene eventos registrados.')).toBeNull()
    expect(screen.getByText('Turno creado')).toBeDefined()
    expect(screen.getByText('Ana Ejemplo · Consulta / control')).toBeDefined()
  })

  it('HIS-2f: una respuesta que llega después de cambiar de día no reabre el panel', async () => {
    const servidor = falso()
    const liberar = servidor.retener('/api/turnos/11/historial')
    const usuario = await abrirAgenda(servidor)
    await usuario.click(botonDeHistorial(ANA))
    await screen.findByText('Cargando historial…')

    await usuario.click(screen.getByRole('button', { name: 'Día siguiente' }))
    await screen.findByText('martes 3 de noviembre de 2026')
    liberar()
    await new Promise((resolver) => setTimeout(resolver, 50))

    expect(screen.queryByRole('complementary', { name: 'Historial del turno' })).toBeNull()
    expect(screen.queryByText('Turno creado')).toBeNull()
  })

  it('HIS-2d: el turno ya no existe', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor, EMAIL_ACTIVA)
    servidor.quitarTurno(11)

    await usuario.click(botonDeHistorial(ANA))

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain('El turno ya no existe (RN-GL-04).')
    expect(screen.queryByText('Turno creado')).toBeNull()
    expect(screen.queryByRole('button', { name: 'Reintentar' })).toBeNull()
    expect(screen.getByRole('table', { name: 'Turnos del día' })).toBeDefined()
  })

  it('HIS-2d: sin permiso se ve el 403 del historial', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor, EMAIL_ACTIVA)
    const renovacionesAntes = servidor.llamadas('POST', '/api/auth/refresh')
    servidor.quitarPermiso(EMAIL_ACTIVA)

    await usuario.click(botonDeHistorial(ANA))

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain('Tu usuario no tiene permiso para ver el historial (RN-AU-05).')
    expect(screen.queryByText('Turno creado')).toBeNull()
    expect(screen.queryByRole('button', { name: 'Reintentar' })).toBeNull()
    expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(renovacionesAntes)
    expect(screen.getByRole('table', { name: 'Turnos del día' })).toBeDefined()
  })

  it('HIS-2e: mientras carga', async () => {
    const servidor = falso()
    servidor.retener('/api/turnos/11/historial')
    const usuario = await abrirAgenda(servidor)

    await usuario.click(botonDeHistorial(ANA))

    expect(await screen.findByText('Cargando historial…')).toBeDefined()
    expect(screen.queryByRole('listitem')).toBeNull()
    expect(screen.queryByText('Turno creado')).toBeNull()
  })

  it('HIS-2e: sin conexión con Reintentar', async () => {
    const servidor = falso()
    const liberar = servidor.retener('/api/turnos/11/historial')
    const usuario = await abrirAgenda(servidor)
    await usuario.click(botonDeHistorial(ANA))
    await screen.findByText('Cargando historial…')
    servidor.caerse()
    liberar()

    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_DE_CONEXION)
    expect(screen.queryByText('Cargando historial…')).toBeNull()
    servidor.recuperar()
    const liberarElReintento = servidor.retener('/api/turnos/11/historial')
    await usuario.click(screen.getByRole('button', { name: 'Reintentar' }))

    expect(await screen.findByText('Cargando historial…')).toBeDefined()
    expect(screen.queryByRole('alert')).toBeNull()
    liberarElReintento()
    expect(await screen.findByText('Turno creado')).toBeDefined()
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('HIS-2e: un 500 muestra el aviso de conexión con Reintentar', async () => {
    const servidor = falso()
    servidor.fallarRuta('/api/turnos/11/historial', 500)
    const usuario = await abrirAgenda(servidor)

    await usuario.click(botonDeHistorial(ANA))

    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_DE_CONEXION)
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeDefined()
    expect(screen.queryByText('Turno creado')).toBeNull()
  })

  it('HIS-2e: con el refresh vigente se renueva sin aviso', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    const renovacionesAntes = servidor.llamadas('POST', '/api/auth/refresh')
    servidor.vencerAccess()

    await usuario.click(botonDeHistorial(ANA))

    expect(await screen.findByText('Turno creado')).toBeDefined()
    expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(renovacionesAntes + 1)
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('HIS-2e: una sesión irrenovable vuelve al inicio de sesión', async () => {
    const servidor = falso()
    const usuario = await abrirAgenda(servidor)
    servidor.vencerAccess()
    servidor.invalidarRefresh()

    await usuario.click(botonDeHistorial(ANA))

    await waitFor(() => expect(screen.getByTestId('lugar').textContent).toBe('/ingresar'))
    expect(screen.queryByText(MENSAJE_DE_CONEXION)).toBeNull()
    expect(screen.queryByText('Turno creado')).toBeNull()
  })
})
