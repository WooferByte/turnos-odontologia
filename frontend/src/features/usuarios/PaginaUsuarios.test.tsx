import { cleanup, render, screen, waitFor, within } from '@testing-library/react'
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

type Usuario = ReturnType<typeof userEvent.setup>

interface DatosDelFormulario {
  email: string
  contrasena: string
  roles?: string[]
}

/** Abre el panel de alta y completa email, contraseña y roles; no pulsa «Guardar». */
async function completarAlta(usuario: Usuario, datos: DatosDelFormulario) {
  await usuario.click(screen.getByRole('button', { name: 'Nuevo usuario' }))
  if (datos.email !== '') await usuario.type(screen.getByLabelText('Email'), datos.email)
  if (datos.contrasena !== '') await usuario.type(screen.getByLabelText('Contraseña inicial'), datos.contrasena)
  for (const rol of datos.roles ?? []) {
    await usuario.click(within(screen.getByRole('group', { name: 'Roles' })).getByRole('checkbox', { name: rol }))
  }
}

const EMAIL_NUEVO = 'turnos@consultorio-demo.test'
const CONTRASENA_NUEVA = 'clave-ficticia-2026'

describe('PaginaUsuarios: alta', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-093 CA-1: alta de una recepcionista', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor, '/panel/usuarios')
    await screen.findByRole('table')

    await completarAlta(usuario, { email: EMAIL_NUEVO, contrasena: CONTRASENA_NUEVA, roles: ['Recepcionista'] })
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => expect(filasDeDatos()).toHaveLength(4))
    expect(servidor.llamadas('POST', '/api/usuarios')).toBe(1)
    expect(servidor.cuerpos('POST', '/api/usuarios')).toEqual([
      { email: EMAIL_NUEVO, contrasena: CONTRASENA_NUEVA, roles: ['recepcionista'] },
    ])
    const nueva = within(filaDe(EMAIL_NUEVO))
    expect(rolesDe(EMAIL_NUEVO)).toEqual(['Recepcionista'])
    expect(nueva.getByText('Activo')).toBeDefined()
    expect(screen.getByText('4 usuarios registrados')).toBeDefined()
    expect(screen.queryByRole('complementary')).toBeNull()

    await usuario.click(screen.getByRole('button', { name: 'Nuevo usuario' }))

    expect(screen.getByLabelText<HTMLInputElement>('Email').value).toBe('')
    expect(screen.getByLabelText<HTMLInputElement>('Contraseña inicial').value).toBe('')
    const casillas = within(screen.getByRole('group', { name: 'Roles' })).getAllByRole<HTMLInputElement>('checkbox')
    expect(casillas.map((casilla) => casilla.checked)).toEqual([false, false, false])
  })
})

const AVISO_SESION_TERMINADA = 'Tu sesión terminó. Iniciá sesión de nuevo.'
const MENSAJE_EMAIL_REPETIDO = 'Ya existe un usuario con ese email (RN-AU-08).'
const MENSAJE_CONTRASENA_CORTA = 'La contraseña debe tener de 10 caracteres a 72 bytes (RN-AU-07).'

describe('PaginaUsuarios: errores del alta', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-093 CA-2: el email repetido se muestra debajo del email', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor, '/panel/usuarios')
    await screen.findByRole('table')

    await completarAlta(usuario, { email: EMAIL_RECEPCIONISTA, contrasena: CONTRASENA_NUEVA, roles: ['Recepcionista'] })
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    const mensaje = await screen.findByText(MENSAJE_EMAIL_REPETIDO)
    const email = screen.getByLabelText<HTMLInputElement>('Email')
    expect(email.getAttribute('aria-describedby')).toBe(mensaje.id)
    expect(email.value).toBe(EMAIL_RECEPCIONISTA)
    expect(screen.getByLabelText<HTMLInputElement>('Contraseña inicial').value).toBe(CONTRASENA_NUEVA)
    expect(screen.getByRole('complementary')).toBeDefined()
    expect(filasDeDatos()).toHaveLength(3)
    expect(servidor.usuariosActuales()).toHaveLength(3)
  })

  it('US-093 CA-9: la contraseña inicial corta se muestra debajo de la contraseña', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor, '/panel/usuarios')
    await screen.findByRole('table')

    await completarAlta(usuario, { email: EMAIL_NUEVO, contrasena: 'corta-123', roles: ['Recepcionista'] })
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    const mensaje = await screen.findByText(MENSAJE_CONTRASENA_CORTA)
    const contrasena = screen.getByLabelText<HTMLInputElement>('Contraseña inicial')
    expect(contrasena.getAttribute('aria-describedby')).toContain(mensaje.id)
    expect(contrasena.minLength).toBe(-1)
    expect(contrasena.maxLength).toBe(-1)
    expect(servidor.llamadas('POST', '/api/usuarios')).toBe(1)
    expect(filasDeDatos()).toHaveLength(3)
  })

  it('US-093 CA-1: un email que la API rechaza se muestra debajo del email', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor, '/panel/usuarios')
    await screen.findByRole('table')
    const largo = `${'a'.repeat(209)}@${'b'.repeat(40)}.test`
    expect(largo).toHaveLength(255)

    await completarAlta(usuario, { email: largo, contrasena: CONTRASENA_NUEVA, roles: ['Recepcionista'] })
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    const mensaje = await screen.findByText('Ingresá un email válido.')
    const email = screen.getByLabelText<HTMLInputElement>('Email')
    expect(email.getAttribute('aria-describedby')).toBe(mensaje.id)
    expect(email.value).toBe(largo)
    expect(servidor.llamadas('POST', '/api/usuarios')).toBe(1)
    expect(screen.getByRole('complementary')).toBeDefined()
    expect(filasDeDatos()).toHaveLength(3)
  })

  it('US-093 CA-1: sin roles, campos vacíos y sin conexión', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor, '/panel/usuarios')
    await screen.findByRole('table')

    await completarAlta(usuario, { email: '', contrasena: CONTRASENA_NUEVA })
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))
    await usuario.type(screen.getByLabelText('Email'), EMAIL_NUEVO)
    await usuario.clear(screen.getByLabelText('Contraseña inicial'))
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))
    expect(servidor.llamadas('POST', '/api/usuarios')).toBe(0)

    await usuario.type(screen.getByLabelText('Contraseña inicial'), CONTRASENA_NUEVA)
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    const mensaje = await screen.findByText('Elegí al menos un rol.')
    expect(screen.getByRole('group', { name: 'Roles' }).getAttribute('aria-describedby')).toBe(mensaje.id)
    expect(servidor.llamadas('POST', '/api/usuarios')).toBe(1)

    await usuario.click(within(screen.getByRole('group', { name: 'Roles' })).getByRole('checkbox', { name: 'Dueño' }))
    servidor.caerse()
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    expect(within(await screen.findByRole('alert')).getByText(MENSAJE_DE_CONEXION)).toBeDefined()
    expect(screen.getByLabelText<HTMLInputElement>('Email').value).toBe(EMAIL_NUEVO)
    expect(screen.getByLabelText<HTMLInputElement>('Contraseña inicial').value).toBe(CONTRASENA_NUEVA)
    expect(screen.getByRole<HTMLInputElement>('checkbox', { name: 'Dueño' }).checked).toBe(true)
    expect((screen.getByRole('button', { name: 'Guardar' }) as HTMLButtonElement).disabled).toBe(false)
    expect(filasDeDatos()).toHaveLength(3)
  })

  it('US-093 CA-1: cerrar el alta borra la contraseña', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor, '/panel/usuarios')
    await screen.findByRole('table')

    await completarAlta(usuario, { email: EMAIL_NUEVO, contrasena: CONTRASENA_NUEVA })
    await usuario.click(screen.getByRole('button', { name: 'Cancelar' }))
    await usuario.click(screen.getByRole('button', { name: 'Nuevo usuario' }))

    expect(servidor.llamadas('POST', '/api/usuarios')).toBe(0)
    expect(screen.getByLabelText<HTMLInputElement>('Email').value).toBe('')
    expect(screen.getByLabelText<HTMLInputElement>('Contraseña inicial').value).toBe('')
    expect(document.body.textContent).not.toContain(CONTRASENA_NUEVA)
  })

  it('US-092 CA-1: una sesión irrenovable al guardar un alta', async () => {
    const servidor = crearServidorFalso()
    const usuario = await abrirPanel(servidor, '/panel/usuarios')
    await screen.findByRole('table')
    await completarAlta(usuario, { email: EMAIL_NUEVO, contrasena: CONTRASENA_NUEVA, roles: ['Recepcionista'] })
    servidor.vencerAccess()
    servidor.invalidarRefresh()

    await usuario.click(screen.getByRole('button', { name: 'Guardar' }))

    expect((await screen.findByRole('status')).textContent).toBe(AVISO_SESION_TERMINADA)
    expect(screen.getByTestId('lugar').textContent).toBe('/ingresar')
    expect(servidor.usuariosActuales()).toHaveLength(3)
  })
})
