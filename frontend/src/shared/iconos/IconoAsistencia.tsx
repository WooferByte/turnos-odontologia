import { Icono } from './Icono'

/** Tilde en un círculo: la acción de registrar la asistencia de un turno. */
export function IconoAsistencia({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <circle cx="12" cy="12" r="10" />
      <path d="M8 12.5l3 3 5-6" />
    </Icono>
  )
}
