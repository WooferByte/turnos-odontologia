// Aviso `role="alert"` con ícono y, si corresponde, un título (D234, T17 de C-11, U19 de C-09). Lo comparten las
// pantallas del panel: cada una decide el mensaje (fijo, nunca el `detail` de la API) y su título.
import type { ReactNode } from 'react'
import { IconoAlerta } from '../iconos/IconoAlerta'

interface Propiedades {
  mensaje: string
  /** Título corto que acompaña al mensaje; `null` si lo repetiría. */
  titulo: string | null
  children?: ReactNode
}

export function Aviso({ mensaje, titulo, children }: Propiedades) {
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
