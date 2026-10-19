// Aviso `role="alert"` con ícono y, si corresponde, un título (D234, T17). El mensaje es el de T11 y no
// cambia; el título solo lo acompaña cuando es corto y distinto del mensaje.
import type { ReactNode } from 'react'
import { IconoAlerta } from '../../shared/iconos/IconoAlerta'
import { tituloDelAviso } from './mensajes'

interface Propiedades {
  mensaje: string
  children?: ReactNode
}

export function Aviso({ mensaje, children }: Propiedades) {
  const titulo = tituloDelAviso(mensaje)
  return (
    <div role="alert" className="aviso aviso-error">
      <IconoAlerta clase="icono icono-aviso" />
      <div className="aviso-texto">
        {titulo === null ? null : <p className="aviso-titulo">{titulo}</p>}
        <p className="aviso-mensaje">{mensaje}</p>
        {children}
      </div>
    </div>
  )
}
