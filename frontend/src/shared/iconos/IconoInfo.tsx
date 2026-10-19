import { Icono } from './Icono'

export function IconoInfo({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5M12 7.800v.1" />
    </Icono>
  )
}
