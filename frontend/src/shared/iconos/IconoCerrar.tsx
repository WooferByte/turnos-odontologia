import { Icono } from './Icono'

export function IconoCerrar({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <path d="M6 6l12 12M18 6L6 18" />
    </Icono>
  )
}
