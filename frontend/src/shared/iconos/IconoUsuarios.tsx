import { Icono } from './Icono'

export function IconoUsuarios({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M2.5 20a6.5 6.5 0 0 1 13 0" />
      <path d="M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14.2a6.5 6.5 0 0 1 3.5 5.8" />
    </Icono>
  )
}
