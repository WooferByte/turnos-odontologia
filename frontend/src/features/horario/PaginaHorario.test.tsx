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
  PROFESIONAL_INACTIVO,
  PROFESIONALES_DE_PARTIDA,
  USUARIOS_DE_PARTIDA,
  USUARIO_DUENO,
  crearServidorFalso,
  type ServidorFalso,
} from '../../test/servidorFalso'

const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
const SUBTITULO = 'Franjas semanales en hora del consultorio (America/Argentina/Buenos_Aires).'
const NOTA_RN_AG_04 =
  'Los turnos solo se pueden crear dentro de una franja (RN-AG-04). Cambiar el horario no modifica los turnos ya dados.'

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

function diaDe(nombre: string): HTMLElement {
  return screen.getByRole('region', { name: nombre })
}

/** Las franjas de un día como «desde-hasta», en el orden en que se ven. */
function franjasDe(nombre: string): string[] {
  const desde = within(diaDe(nombre)).queryAllByLabelText<HTMLInputElement>('Desde')
  const hasta = within(diaDe(nombre)).queryAllByLabelText<HTMLInputElement>('Hasta')
  return desde.map((entrada, i) => `${entrada.value}-${hasta[i]?.value ?? ''}`)
}

const MANANA_Y_TARDE = ['09:00-13:00', '15:00-19:00']

describe('PaginaHorario: la semana', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-002 CA-1: la odontóloga ve la semana de la demo', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor)
    await screen.findByText('Panel del consultorio')

    await usuario.click(screen.getByRole('link', { name: 'Horario' }))

    await screen.findByRole('region', { name: 'Lunes' })
    expect(screen.getByTestId('lugar').textContent).toBe('/panel/horario')
    expect(screen.getByRole('combobox', { name: 'Profesional' })).toHaveProperty('value', '1')
    expect(screen.getByRole('option', { name: 'Dra. Demo Ficticia' })).toBeDefined()
    for (const dia of DIAS.slice(0, 5)) expect(franjasDe(dia)).toEqual(MANANA_Y_TARDE)
    for (const dia of DIAS.slice(5)) {
      expect(franjasDe(dia)).toEqual([])
      expect(within(diaDe(dia)).getByText('Sin atención')).toBeDefined()
    }
    expect(screen.getByText(SUBTITULO)).toBeDefined()
    expect(screen.getByText(NOTA_RN_AG_04)).toBeDefined()
    expect(servidor.llamadas('GET', '/api/profesionales')).toBe(1)
    expect(servidor.llamadas('GET', '/api/profesionales/1/horario')).toBe(1)
  })

  it('US-002 CA-1: la recepcionista y el dueño ven la semana', async () => {
    const catalogo = [...USUARIOS_DE_PARTIDA, USUARIO_DUENO]
    for (const email of [EMAIL_RECEPCIONISTA, EMAIL_DUENO]) {
      sessionStorage.clear()
      await abrirPanel(crearServidorFalso({ usuarios: catalogo }), '/panel/horario', email)

      await screen.findByRole('region', { name: 'Lunes' })
      expect(franjasDe('Viernes')).toEqual(MANANA_Y_TARDE)
      expect(franjasDe('Sábado')).toEqual([])
      cleanup()
    }
  })
})

describe('PaginaHorario: carga, conexión y profesional', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-002 CA-1: mientras carga y sin conexión', async () => {
    const servidor = crearServidorFalso()
    const liberar = servidor.retener('/api/profesionales')
    await abrirPanel(servidor, '/panel/horario')

    expect(await screen.findByText('Cargando horario…')).toBeDefined()
    expect(screen.queryByRole('region', { name: 'Lunes' })).toBeNull()
    liberar()
    await screen.findByRole('region', { name: 'Lunes' })
    expect(screen.queryByText('Cargando horario…')).toBeNull()
  })

  it('US-002 CA-1: sin conexión muestra el mensaje y Reintentar recupera la semana', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor)
    await screen.findByText('Panel del consultorio')
    servidor.caerse()

    await usuario.click(screen.getByRole('link', { name: 'Horario' }))

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain('No se pudo conectar con el servidor. Probá de nuevo en unos minutos.')
    expect(screen.queryByRole('region', { name: 'Lunes' })).toBeNull()
    servidor.recuperar()
    await usuario.click(screen.getByRole('button', { name: 'Reintentar' }))

    await screen.findByRole('region', { name: 'Lunes' })
    expect(franjasDe('Lunes')).toEqual(MANANA_Y_TARDE)
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('US-002 CA-1: elegir otro profesional muestra su horario', async () => {
    const servidor = crearServidorFalso({ profesionales: [...PROFESIONALES_DE_PARTIDA, PROFESIONAL_INACTIVO] })
    const usuario = await abrirPanel(servidor, '/panel/horario')
    await screen.findByRole('region', { name: 'Lunes' })
    expect(franjasDe('Lunes')).toEqual(MANANA_Y_TARDE)

    await usuario.selectOptions(screen.getByRole('combobox', { name: 'Profesional' }), 'Dr. Ejemplo Ficticio (inactivo)')

    await waitFor(() => expect(franjasDe('Lunes')).toEqual([]))
    for (const dia of DIAS) expect(within(diaDe(dia)).getByText('Sin atención')).toBeDefined()
    expect(servidor.llamadas('GET', '/api/profesionales/2/horario')).toBe(1)
    expect(servidor.llamadas('GET', '/api/profesionales')).toBe(1)
  })

  it('US-002 CA-1: sin profesionales activos se elige el primero de la lista', async () => {
    const servidor = crearServidorFalso({ profesionales: [...PROFESIONALES_DE_PARTIDA, PROFESIONAL_INACTIVO] })
    servidor.marcarInactivo(1)
    await abrirPanel(servidor, '/panel/horario')

    await screen.findByRole('region', { name: 'Lunes' })
    expect(screen.getByRole('combobox', { name: 'Profesional' })).toHaveProperty('value', '1')
    expect(screen.getByRole('option', { name: 'Dra. Demo Ficticia (inactivo)' })).toBeDefined()
    expect(franjasDe('Lunes')).toEqual(MANANA_Y_TARDE)
    expect(servidor.llamadas('GET', '/api/profesionales/1/horario')).toBe(1)
    expect(servidor.llamadas('GET', '/api/profesionales/2/horario')).toBe(0)
  })
})

type Usuario = ReturnType<typeof userEvent.setup>

const MENSAJE_RN_AG_16 = 'Hay franjas que se superponen o no terminan después de empezar (RN-AG-16).'
const RUTA_DEL_PUT = '/api/profesionales/1/horario'

function gruposDe(dia: string): HTMLElement[] {
  return within(diaDe(dia)).queryAllByRole('group')
}

/** Pulsa «Agregar franja» del día y escribe las horas que se pidan en la franja nueva (la última del día). */
async function agregarFranja(usuario: Usuario, dia: string, desde: string | null, hasta: string | null) {
  await usuario.click(within(diaDe(dia)).getByRole('button', { name: 'Agregar franja' }))
  const nueva = gruposDe(dia).at(-1)
  if (nueva === undefined) throw new Error(`No se agregó la franja de ${dia}`)
  if (desde !== null) await usuario.type(within(nueva).getByLabelText('Desde'), desde)
  if (hasta !== null) await usuario.type(within(nueva).getByLabelText('Hasta'), hasta)
}

function marcadaComoInvalida(grupo: HTMLElement): boolean {
  return within(grupo)
    .getAllByLabelText(/^(Desde|Hasta)$/)
    .every((entrada) => entrada.getAttribute('aria-invalid') === 'true')
}

const HORARIO_DE_LA_DEMO_EN_ORDEN = [0, 1, 2, 3, 4].flatMap((dia) => [
  { dia_semana: dia, hora_inicio: '09:00', hora_fin: '13:00' },
  { dia_semana: dia, hora_inicio: '15:00', hora_fin: '19:00' },
])

describe('PaginaHorario: editar y guardar', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-002 CA-1: agregar la mañana del sábado y guardar', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor, '/panel/horario')
    await screen.findByRole('region', { name: 'Lunes' })

    await agregarFranja(usuario, 'Sábado', '09:00', '12:00')
    await usuario.click(screen.getByRole('button', { name: 'Guardar horario' }))

    expect(await screen.findByText('Horario guardado.')).toBeDefined()
    expect(servidor.cuerpos('PUT', RUTA_DEL_PUT)).toEqual([
      { franjas: [...HORARIO_DE_LA_DEMO_EN_ORDEN, { dia_semana: 5, hora_inicio: '09:00', hora_fin: '12:00' }] },
    ])
    expect(servidor.llamadas('PUT', RUTA_DEL_PUT)).toBe(1)
    expect(franjasDe('Sábado')).toEqual(['09:00-12:00'])
    expect(within(diaDe('Sábado')).queryByText('Sin atención')).toBeNull()
  })

  it('HOR-1: dos franjas superpuestas del miércoles', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor, '/panel/horario')
    await screen.findByRole('region', { name: 'Lunes' })

    await agregarFranja(usuario, 'Miércoles', '12:00', '16:00')
    await usuario.click(screen.getByRole('button', { name: 'Guardar horario' }))

    await screen.findByText(MENSAJE_RN_AG_16)
    expect(franjasDe('Miércoles')).toEqual(['09:00-13:00', '15:00-19:00', '12:00-16:00'])
    expect(gruposDe('Miércoles').map(marcadaComoInvalida)).toEqual([false, true, true])
    expect(within(diaDe('Miércoles')).getAllByText(MENSAJE_RN_AG_16)).toHaveLength(1)
    expect(screen.getAllByText(MENSAJE_RN_AG_16)).toHaveLength(1)
    expect(screen.queryByText('Horario guardado.')).toBeNull()
    expect(servidor.horarioActual(1)).toHaveLength(10)
  })
})

const AVISO_SESION_TERMINADA = 'Tu sesión terminó. Iniciá sesión de nuevo.'
const MENSAJE_DE_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'

function botonGuardar(): HTMLButtonElement {
  return screen.getByRole<HTMLButtonElement>('button', { name: 'Guardar horario' })
}

describe('PaginaHorario: bordes del guardado y rechazos', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-002 CA-1: quitar la tarde del viernes y guardar', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor, '/panel/horario')
    await screen.findByRole('region', { name: 'Lunes' })

    const tardeDelViernes = gruposDe('Viernes')[1]
    if (tardeDelViernes === undefined) throw new Error('El viernes no tiene tarde')
    await usuario.click(within(tardeDelViernes).getByRole('button', { name: 'Quitar franja' }))
    await usuario.click(botonGuardar())

    await screen.findByText('Horario guardado.')
    expect(servidor.cuerpos('PUT', RUTA_DEL_PUT)).toEqual([{ franjas: HORARIO_DE_LA_DEMO_EN_ORDEN.slice(0, 9) }])
    expect(franjasDe('Viernes')).toEqual(['09:00-13:00'])
    expect(franjasDe('Jueves')).toEqual(MANANA_Y_TARDE)
  })

  it('US-002 CA-1: guardar sin cambios o con una franja incompleta no manda nada', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor, '/panel/horario')
    await screen.findByRole('region', { name: 'Lunes' })

    await usuario.click(botonGuardar())
    expect(servidor.llamadas('PUT', RUTA_DEL_PUT)).toBe(0)
    expect(screen.queryByText('Horario guardado.')).toBeNull()
    expect(screen.queryByText('Completá las dos horas de la franja.')).toBeNull()

    await agregarFranja(usuario, 'Domingo', '10:00', null)
    await usuario.click(botonGuardar())

    expect(servidor.llamadas('PUT', RUTA_DEL_PUT)).toBe(0)
    expect(within(diaDe('Domingo')).getByText('Completá las dos horas de la franja.')).toBeDefined()
    expect(within(diaDe('Domingo')).getByLabelText('Desde').getAttribute('aria-invalid')).toBeNull()
    expect(within(diaDe('Domingo')).getByLabelText('Hasta').getAttribute('aria-invalid')).toBe('true')
  })

  it('US-002 CA-1: guardar dos veces seguidas manda un solo pedido', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor, '/panel/horario')
    await screen.findByRole('region', { name: 'Lunes' })
    await agregarFranja(usuario, 'Sábado', '09:00', '12:00')
    const liberar = servidor.retener(RUTA_DEL_PUT)

    await usuario.click(botonGuardar())
    await waitFor(() => expect(botonGuardar().disabled).toBe(true))
    await usuario.click(botonGuardar())

    expect(servidor.llamadas('PUT', RUTA_DEL_PUT)).toBe(1)
    liberar()
    expect(await screen.findByText('Horario guardado.')).toBeDefined()
    expect(servidor.llamadas('PUT', RUTA_DEL_PUT)).toBe(1)
    expect(botonGuardar().disabled).toBe(false)
  })

  it('US-002 CA-1: sin conexión al guardar se conserva lo editado', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor, '/panel/horario')
    await screen.findByRole('region', { name: 'Lunes' })
    await agregarFranja(usuario, 'Sábado', '09:00', '12:00')
    servidor.caerse()

    await usuario.click(botonGuardar())

    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_DE_CONEXION)
    expect(screen.queryByRole('button', { name: 'Reintentar' })).toBeNull()
    expect(screen.queryByText('Horario guardado.')).toBeNull()
    expect(franjasDe('Sábado')).toEqual(['09:00-12:00'])
    expect(botonGuardar().disabled).toBe(false)
  })

  it('HOR-1: una franja invertida se marca con el mensaje de RN-AG-16', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor, '/panel/horario')
    await screen.findByRole('region', { name: 'Lunes' })

    await agregarFranja(usuario, 'Sábado', '12:00', '09:00')
    await usuario.click(botonGuardar())

    await within(diaDe('Sábado')).findByText(MENSAJE_RN_AG_16)
    expect(servidor.llamadas('PUT', RUTA_DEL_PUT)).toBe(1)
    expect(gruposDe('Sábado').map(marcadaComoInvalida)).toEqual([true])
    for (const dia of DIAS.slice(0, 5)) expect(gruposDe(dia).some(marcadaComoInvalida)).toBe(false)
    expect(screen.getAllByText(MENSAJE_RN_AG_16)).toHaveLength(1)
    expect(screen.queryByText('Horario guardado.')).toBeNull()
  })

  it('US-002 CA-1: un rechazo de formato sin código', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor, '/panel/horario')
    await screen.findByRole('region', { name: 'Lunes' })
    // 61 franjas de media hora que no se superponen: sábado y domingo a cada hora, lunes 00-08 y martes 00-05.
    const destinos: [string, number][] = [
      ['Sábado', 24],
      ['Domingo', 24],
      ['Lunes', 8],
      ['Martes', 5],
    ]
    for (const [dia, cantidad] of destinos) {
      for (let hora = 0; hora < cantidad; hora += 1) {
        const texto = String(hora).padStart(2, '0')
        fireEvent.click(within(diaDe(dia)).getByRole('button', { name: 'Agregar franja' }))
        const nueva = gruposDe(dia).at(-1) as HTMLElement
        fireEvent.change(within(nueva).getByLabelText('Desde'), { target: { value: `${texto}:00` } })
        fireEvent.change(within(nueva).getByLabelText('Hasta'), { target: { value: `${texto}:30` } })
      }
    }

    await usuario.click(botonGuardar())

    expect((await screen.findByRole('alert')).textContent).toContain('Revisá las franjas del horario.')
    expect(servidor.llamadas('PUT', RUTA_DEL_PUT)).toBe(1)
    expect(servidor.cuerpos('PUT', RUTA_DEL_PUT)[0]?.franjas).toHaveLength(71)
    expect(gruposDe('Sábado')).toHaveLength(24)
    expect(screen.queryByText('Horario guardado.')).toBeNull()
    expect(servidor.horarioActual(1)).toHaveLength(10)
  })

  it('US-002 CA-1: la recepcionista intenta guardar', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor, '/panel/horario', EMAIL_RECEPCIONISTA)
    await screen.findByRole('region', { name: 'Lunes' })
    const refrescosAntes = servidor.llamadas('POST', '/api/auth/refresh')
    await agregarFranja(usuario, 'Sábado', '09:00', '12:00')

    await usuario.click(botonGuardar())

    expect((await screen.findByRole('alert')).textContent).toContain(
      'Tu usuario no tiene permiso para modificar el horario (RN-AU-05).',
    )
    expect(servidor.llamadas('POST', '/api/auth/refresh')).toBe(refrescosAntes)
    expect(screen.getByTestId('lugar').textContent).toBe('/panel/horario')
    expect(servidor.horarioActual(1).some((f) => f.dia_semana === 5)).toBe(false)
  })

  it('US-002 CA-1: un profesional que ya no existe', async () => {
    const servidor = crearServidorFalso({ profesionales: [...PROFESIONALES_DE_PARTIDA, PROFESIONAL_INACTIVO] })
    const usuario = await abrirPanel(servidor, '/panel/horario')
    await screen.findByRole('region', { name: 'Lunes' })
    await agregarFranja(usuario, 'Sábado', '09:00', '12:00')
    servidor.quitarProfesional(1)

    await usuario.click(botonGuardar())

    await screen.findByRole('option', { name: 'Dr. Ejemplo Ficticio (inactivo)' })
    expect(servidor.llamadas('GET', '/api/profesionales')).toBe(2)
    expect(screen.queryByRole('option', { name: 'Dra. Demo Ficticia' })).toBeNull()
    expect(screen.getByRole('alert').textContent).toContain('El profesional ya no existe (RN-GL-04).')
  })

  it('US-092 CA-1: una sesión irrenovable al guardar el horario', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor, '/panel/horario')
    await screen.findByRole('region', { name: 'Lunes' })
    await agregarFranja(usuario, 'Sábado', '09:00', '12:00')
    servidor.vencerAccess()
    servidor.invalidarRefresh()

    await usuario.click(botonGuardar())

    expect((await screen.findByRole('status')).textContent).toBe(AVISO_SESION_TERMINADA)
    expect(screen.getByTestId('lugar').textContent).toBe('/ingresar')
    expect(screen.queryByText(MENSAJE_DE_CONEXION)).toBeNull()
    expect(servidor.horarioActual(1)).toHaveLength(10)
  })

  it('US-002 CA-1: cambiar de profesional descarta lo editado', async () => {
    const servidor = crearServidorFalso({ profesionales: [...PROFESIONALES_DE_PARTIDA, PROFESIONAL_INACTIVO] })
    const usuario = await abrirPanel(servidor, '/panel/horario')
    await screen.findByRole('region', { name: 'Lunes' })
    await agregarFranja(usuario, 'Sábado', '09:00', '12:00')
    const selector = screen.getByRole('combobox', { name: 'Profesional' })

    await usuario.selectOptions(selector, 'Dr. Ejemplo Ficticio (inactivo)')
    await waitFor(() => expect(franjasDe('Lunes')).toEqual([]))
    await usuario.selectOptions(screen.getByRole('combobox', { name: 'Profesional' }), 'Dra. Demo Ficticia')

    await waitFor(() => expect(franjasDe('Lunes')).toEqual(MANANA_Y_TARDE))
    expect(franjasDe('Sábado')).toEqual([])
    expect(servidor.llamadas('PUT', RUTA_DEL_PUT)).toBe(0)
  })
})
