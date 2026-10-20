import { Icono } from './Icono'

export function IconoEspera({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <circle cx="12" cy="12" r="9" opacity="0.3" />
      <path d="M21 12a9 9 0 0 0-9-9" />
    </Icono>
  )
}
