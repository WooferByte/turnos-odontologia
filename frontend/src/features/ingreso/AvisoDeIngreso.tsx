// Aviso de la pantalla de inicio de sesión (C-49, design L4): ícono y un único mensaje, sin título ni código,
// para que el `textContent` del aviso sea exactamente el mensaje fijo (RN-AU-04). No es `Aviso` de prestaciones,
// que agrega un título.
import { IconoAlerta } from '../../shared/iconos/IconoAlerta'
import { IconoInfo } from '../../shared/iconos/IconoInfo'

interface Propiedades {
  tipo: 'error' | 'informativo'
  mensaje: string
}

export function AvisoDeIngreso({ tipo, mensaje }: Propiedades) {
  const esError = tipo === 'error'
  return (
    <div role={esError ? 'alert' : 'status'} className={esError ? 'aviso aviso-error' : 'aviso aviso-informativo'}>
      {esError ? <IconoAlerta clase="icono icono-aviso" /> : <IconoInfo clase="icono icono-aviso" />}
      <p>{mensaje}</p>
    </div>
  )
}
