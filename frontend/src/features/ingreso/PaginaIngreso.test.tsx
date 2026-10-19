import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { App } from '../../App'
import { CONTRASENA_FICTICIA, EMAIL_ACTIVA, crearServidorFalso, type ServidorFalso } from '../../test/servidorFalso'

function montar(ruta: string, servidor: ServidorFalso) {
  render(
    <MemoryRouter initialEntries={[ruta]}>
      <App fetch={servidor.fetch} />
    </MemoryRouter>,
  )
  return userEvent.setup()
}

describe('PaginaIngreso', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-090 CA-1: credenciales válidas llevan al panel', async () => {
    const servidor = crearServidorFalso()
    const usuario = montar('/ingresar', servidor)

    await usuario.type(screen.getByLabelText('Email'), EMAIL_ACTIVA)
    await usuario.type(screen.getByLabelText('Contraseña'), CONTRASENA_FICTICIA)
    await usuario.click(screen.getByRole('button', { name: 'Ingresar' }))

    expect(await screen.findByText('Panel del consultorio')).toBeDefined()
    expect(screen.getByRole('button', { name: 'Cerrar sesión' })).toBeDefined()
    expect(servidor.peticiones('/api/auth/login')).toBe(1)
  })
})
