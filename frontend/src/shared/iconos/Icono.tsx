// Base de los íconos del panel (D234, T17): SVG en línea, decorativos y sin recursos externos (la CSP de
// nginx es `default-src 'self'`). El nombre accesible lo da siempre el texto o el botón que los contiene.
import type { ReactNode } from 'react'

interface Propiedades {
  children: ReactNode
  clase?: string | undefined
}

export function Icono({ children, clase = 'icono' }: Propiedades) {
  return (
    <svg
      className={clase}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {children}
    </svg>
  )
}
