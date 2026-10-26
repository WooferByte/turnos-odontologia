import { Icono } from './Icono'

export function IconoCalendario({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <path d="M16 2v4M8 2v4M3 10h18" />
    </Icono>
  )
}
