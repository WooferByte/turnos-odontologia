import { Icono } from './Icono'

export function IconoLlave({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <circle cx="7.5" cy="15.5" r="4.5" />
      <path d="M10.7 12.3L21 2M16 7l3 3M14 9l2 2" />
    </Icono>
  )
}
