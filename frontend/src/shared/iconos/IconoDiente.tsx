import { Icono } from './Icono'

export function IconoDiente({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <path d="M7.5 3C4.9 3 3 5 3 7.6c0 2.2 1 3.6 1.5 6.2.5 2.6.9 7.2 3 7.2 1.7 0 1.6-4.2 3-5h3c1.4.8 1.3 5 3 5 2.1 0 2.5-4.6 3-7.2.5-2.6 1.5-4 1.5-6.2C21 5 19.1 3 16.5 3c-1.8 0-2.7 1-4.5 1S9.3 3 7.5 3z" />
    </Icono>
  )
}
