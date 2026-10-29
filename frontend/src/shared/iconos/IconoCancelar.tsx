import { Icono } from './Icono'

/** Círculo con una X: la acción de cancelar un turno. */
export function IconoCancelar({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <circle cx="12" cy="12" r="10" />
      <path d="M15 9l-6 6M9 9l6 6" />
    </Icono>
  )
}
