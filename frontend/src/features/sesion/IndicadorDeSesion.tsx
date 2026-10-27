// Quién inició sesión (design Y8 a Y13, D308 a D310): el email y los roles que informa `GET /api/auth/yo`,
// pedido una vez al montarse el panel. No muestra nada mientras espera ni si el pedido falla (la sesión sigue):
// un `401` sin renovación posible ya lo resuelve el proveedor de sesión. Los datos viven solo en este estado.
import { useEffect, useState } from 'react'
import { useSesionDelPanel } from '../../shared/api/ProveedorDeSesion'
import { IconoPersona } from '../../shared/iconos/IconoPersona'
import { nombreDelRol } from '../../shared/roles'
import { obtenerUsuarioDeLaSesion, type UsuarioDeLaSesion } from './apiSesion'

const SEPARADOR_DE_ROLES = ' · '

export function IndicadorDeSesion() {
  const { pedidoDelPanel } = useSesionDelPanel()
  const [usuario, setUsuario] = useState<UsuarioDeLaSesion | null>(null)

  useEffect(() => {
    let vigente = true
    obtenerUsuarioDeLaSesion(pedidoDelPanel).then(
      (obtenido) => {
        if (vigente) setUsuario(obtenido)
      },
      () => undefined,
    )
    return () => {
      vigente = false
    }
  }, [pedidoDelPanel])

  if (usuario === null) return null
  return (
    <div className="usuario-de-la-sesion">
      <span className="usuario-de-la-sesion-avatar">
        <IconoPersona />
      </span>
      <p className="usuario-de-la-sesion-texto">
        <span className="usuario-de-la-sesion-email" title={usuario.email}>
          {usuario.email}
        </span>
        <span className="usuario-de-la-sesion-roles">{usuario.roles.map(nombreDelRol).join(SEPARADOR_DE_ROLES)}</span>
      </p>
    </div>
  )
}
