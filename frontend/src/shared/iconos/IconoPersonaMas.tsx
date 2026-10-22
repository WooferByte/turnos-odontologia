import { Icono } from './Icono'

export function IconoPersonaMas({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M2.5 20a6.5 6.5 0 0 1 13 0" />
      <path d="M19 8v6M16 11h6" />
    </Icono>
  )
}
