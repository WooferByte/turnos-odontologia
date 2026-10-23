import { Icono } from './Icono'

export function IconoPapelera({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <path d="M4 7h16M10 11v6M14 11v6" />
      <path d="M6 7l1 12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-12M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
    </Icono>
  )
}
