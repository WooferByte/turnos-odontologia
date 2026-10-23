import { Icono } from './Icono'

export function IconoGuardar({ clase }: { clase?: string | undefined }) {
  return (
    <Icono clase={clase}>
      <path d="M5 4h11l3 3v12a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1z" />
      <path d="M8 4v5h7V4M8 20v-6h8v6" />
    </Icono>
  )
}
