import { Icono } from './Icono'

export function IconoMaletin({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <rect x="3" y="7" width="18" height="13" rx="2" />
      <path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
      <path d="M12 11v6M9 14h6" />
    </Icono>
  )
}
