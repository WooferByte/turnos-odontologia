import { Icono } from './Icono'

export function IconoAlerta({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7.500v5M12 16.200v.1" />
    </Icono>
  )
}
