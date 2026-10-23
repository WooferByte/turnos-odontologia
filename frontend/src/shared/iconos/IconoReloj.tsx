import { Icono } from './Icono'

export function IconoReloj({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </Icono>
  )
}
