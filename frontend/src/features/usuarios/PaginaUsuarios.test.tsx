import { cleanup, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { App } from '../../App'
import { CLAVE_DE_SESION } from '../../shared/api/sesion'
import {
  EMAIL_ACTIVA,
  EMAIL_ADMINISTRACION,
  EMAIL_DUENO,
  EMAIL_RECEPCIONISTA,
  PRESTACIONES_DE_PARTIDA,
  USUARIOS_DE_PARTIDA,
  USUARIO_DUENO,
  crearServidorFalso,
  type ServidorFalso,
} from '../../test/servidorFalso'

const MENSAJE_DE_CONEXION = 'No se pudo conectar con el servidor. Probá de nuevo en unos minutos.'
const MENSAJE_SIN_PERMISO_DE_LECTURA = 'Tu usuario no tiene permiso para ver los usuarios (RN-AU-05).'

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

function filasDeDatos(): HTMLTableRowElement[] {
  return within(screen.getByRole('table')).getAllByRole<HTMLTableRowElement>('row').slice(1)
}

function filaDe(email: string): HTMLElement {
  // La fila que se está editando lleva la marca «Editando» dentro de la celda del email.
  const fila = screen.getByRole('cell', { name: (n) => n === email || n === `${email} Editando` }).closest('tr')
  if (fila === null) throw new Error(`No hay fila para ${email}`)
  return fila
}

function rolesDe(email: string): string[] {
  return within(filaDe(email))
    .getAllByRole('listitem')
    .map((rol) => rol.textContent ?? '')
}

describe('PaginaUsuarios: listado', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-093 CA-1: la odontóloga ve los tres usuarios', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor)
    await screen.findByText('Panel del consultorio')

    await usuario.click(screen.getByRole('link', { name: 'Usuarios' }))

    await screen.findByRole('table')
    expect(screen.getByTestId('lugar').textContent).toBe('/panel/usuarios')
    expect(filasDeDatos().map((fila) => fila.cells[0]?.textContent)).toEqual([
      EMAIL_ACTIVA,
      EMAIL_RECEPCIONISTA,
      EMAIL_ADMINISTRACION,
    ])
    expect(rolesDe(EMAIL_ACTIVA)).toEqual(['Odontólogo', 'Dueño'])
    expect(rolesDe(EMAIL_RECEPCIONISTA)).toEqual(['Recepcionista'])
    expect(rolesDe(EMAIL_ADMINISTRACION)).toEqual(['Dueño'])
    const odontologa = within(filaDe(EMAIL_ACTIVA))
    expect(odontologa.getByText('Activo')).toBeDefined()
    expect(odontologa.getByRole('button', { name: `Editar ${EMAIL_ACTIVA}` })).toBeDefined()
    expect(odontologa.getByRole('button', { name: `Desactivar ${EMAIL_ACTIVA}` })).toBeDefined()
    const inactivo = filaDe(EMAIL_ADMINISTRACION)
    expect(inactivo.className).toContain('inactiva')
    expect(within(inactivo).getByText('Inactivo')).toBeDefined()
    expect(within(inactivo).getByRole('button', { name: `Reactivar ${EMAIL_ADMINISTRACION}` })).toBeDefined()
    expect(screen.getByText('3 usuarios registrados')).toBeDefined()
    expect(servidor.llamadas('GET', '/api/usuarios')).toBe(1)
  })

  it('US-093 CA-1: la recepcionista no ve los usuarios', async () => {
    const servidor = crearServidorFalso({ prestaciones: PRESTACIONES_DE_PARTIDA })
    const usuario = await abrirPanel(servidor, '/panel/usuarios', EMAIL_RECEPCIONISTA)

    const aviso = await screen.findByRole('alert')

    expect(aviso.textContent).toContain(MENSAJE_SIN_PERMISO_DE_LECTURA)
    expect(screen.queryByRole('table')).toBeNull()
    expect(screen.queryByText(/usuarios registrados/)).toBeNull()
    expect(screen.queryByRole('button', { name: 'Nuevo usuario' })).toBeNull()
    await usuario.click(screen.getByRole('link', { name: 'Prestaciones' }))
    await screen.findByRole('table')
    expect(screen.getByTestId('lugar').textContent).toBe('/panel/prestaciones')
  })

  it('US-093 CA-1: mientras carga y sin conexión', async () => {
    const servidor = crearServidorFalso()
    const liberar = servidor.retener('/api/usuarios')
    const usuario = await abrirPanel(servidor, '/panel/usuarios')

    expect(await screen.findByText('Cargando usuarios…')).toBeDefined()
    expect(screen.queryByRole('table')).toBeNull()
    expect(screen.queryByText(/usuarios registrados/)).toBeNull()
    servidor.caerse()
    liberar()

    expect((await screen.findByRole('alert')).textContent).toContain(MENSAJE_DE_CONEXION)
    expect(screen.queryByText('Cargando usuarios…')).toBeNull()
    servidor.recuperar()
    await usuario.click(screen.getByRole('button', { name: 'Reintentar' }))

    await screen.findByRole('table')
    expect(filasDeDatos()).toHaveLength(3)
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('US-093 CA-1: el dueño ve la tabla', async () => {
    const catalogo = [USUARIOS_DE_PARTIDA[0], USUARIOS_DE_PARTIDA[1], USUARIO_DUENO].flatMap((u) => (u ? [u] : []))
    await abrirPanel(crearServidorFalso({ usuarios: catalogo }), '/panel/usuarios', EMAIL_DUENO)

    await screen.findByRole('table')

    expect(filasDeDatos()).toHaveLength(3)
    expect(screen.getByText('3 usuarios registrados')).toBeDefined()
  })
})
