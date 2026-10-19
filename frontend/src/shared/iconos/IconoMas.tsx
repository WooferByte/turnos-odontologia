import { Icono } from './Icono'

export function IconoMas({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <path d="M12 5v14M5 12h14" />
    </Icono>
  )
}
