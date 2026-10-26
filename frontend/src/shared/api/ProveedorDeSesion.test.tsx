import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { crearServidorFalso } from '../../test/servidorFalso'
import { ProveedorDeSesion, useSesionDelPanel } from './ProveedorDeSesion'
import { CLAVE_DE_SESION } from './sesion'

function Consumidor() {
  const { estado, aviso, reemplazarTokens } = useSesionDelPanel()
  return (
    <div>
      <p data-testid="estado">{estado}</p>
      <p data-testid="aviso">{aviso ?? 'ninguno'}</p>
      <button type="button" onClick={() => reemplazarTokens('acceso-nuevo', 'refresco-nuevo')}>
        Reemplazar
      </button>
    </div>
  )
}

describe('ProveedorDeSesion', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })
  afterEach(() => {
    cleanup()
  })

  it('US-093 CA-7: reemplazarTokens guarda el refresh nuevo sin cambiar el estado', async () => {
    const servidor = crearServidorFalso()
    sessionStorage.setItem(CLAVE_DE_SESION, JSON.stringify({ refresh: servidor.emitirSesion().refresh }))
    render(
      <ProveedorDeSesion fetch={servidor.fetch}>
        <Consumidor />
      </ProveedorDeSesion>,
    )
    await waitFor(() => expect(screen.getByTestId('estado').textContent).toBe('con-sesion'))

    await userEvent.setup().click(screen.getByRole('button', { name: 'Reemplazar' }))

    expect(JSON.parse(sessionStorage.getItem(CLAVE_DE_SESION) ?? 'null')).toEqual({ refresh: 'refresco-nuevo' })
    expect(screen.getByTestId('estado').textContent).toBe('con-sesion')
    expect(screen.getByTestId('aviso').textContent).toBe('ninguno')
  })
})
