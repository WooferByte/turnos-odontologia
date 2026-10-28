import { Icono } from './Icono'

interface Propiedades {
  hacia: 'izquierda' | 'derecha'
  clase?: string | undefined
}

export function IconoFlecha({ hacia, clase }: Propiedades) {
  return (
    <Icono clase={clase}>
      <path d={hacia === 'izquierda' ? 'M15 18l-6-6 6-6' : 'M9 18l6-6-6-6'} />
    </Icono>
  )
}
