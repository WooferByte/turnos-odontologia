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
