import { Icono } from './Icono'

export function IconoLapiz({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <path d="M4 20h4L19 9l-4-4L4 16v4z" />
      <path d="M13.5 6.5l4 4" />
    </Icono>
  )
}
