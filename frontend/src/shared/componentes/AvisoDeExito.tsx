// Aviso de éxito `role="status"` con ícono (D234, C-10): el verde suave de las pantallas del panel. Cada pantalla
// decide el mensaje (fijo, nunca el `detail` de la API).
import { IconoCheck } from '../iconos/IconoCheck'

export function AvisoDeExito({ mensaje }: { mensaje: string }) {
  return (
    <div role="status" className="aviso-exito aviso-de-exito">
      <IconoCheck clase="icono icono-exito" />
      <p>{mensaje}</p>
    </div>
  )
}
