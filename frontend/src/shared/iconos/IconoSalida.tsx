import { Icono } from './Icono'

export function IconoSalida({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <path d="M9 21H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3" />
      <path d="M16 17l5-5-5-5M21 12H10" />
    </Icono>
  )
}
