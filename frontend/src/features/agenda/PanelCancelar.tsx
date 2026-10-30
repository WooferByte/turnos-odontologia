// Panel lateral «Cancelar turno» (design X10, X11): pregunta quién pidió la cancelación, sin opción marcada, y manda
// el estado elegido. No evalúa reglas: las decide la API.
import { IconoCancelar } from '../../shared/iconos/IconoCancelar'
import type { EstadoDeCancelacion, TurnoDeLaAgenda } from './apiAgenda'
import {
  AYUDA_DE_CANCELACION,
  MENSAJE_ELEGI_QUIEN_PIDIO,
  OPCION_EL_CONSULTORIO,
  OPCION_EL_PACIENTE,
  PREGUNTA_DE_CANCELACION,
} from './mensajes'
import { PanelDeDecision, type OpcionDeDecision } from './PanelDeDecision'

interface Propiedades {
  turno: TurnoDeLaAgenda
  zonaHoraria: string
  enviando: boolean
  /** Rechazo de la API ya traducido a su texto fijo; `null` si no hay. */
  error: string | null
  onCancelarTurno(estado: EstadoDeCancelacion): void
  /** Cierra el panel sin pedir nada («Volver» y «Cerrar»). */
  onVolver(): void
}

const OPCIONES: readonly OpcionDeDecision<EstadoDeCancelacion>[] = [
  { estado: 'cancelado_paciente', texto: OPCION_EL_PACIENTE },
  { estado: 'cancelado_profesional', texto: OPCION_EL_CONSULTORIO },
]

export function PanelCancelar({ turno, zonaHoraria, enviando, error, onCancelarTurno, onVolver }: Propiedades) {
  return (
    <PanelDeDecision
      clase="panel-de-cancelar"
      titulo="Cancelar turno"
      icono={<IconoCancelar />}
      turno={turno}
      zonaHoraria={zonaHoraria}
      pregunta={PREGUNTA_DE_CANCELACION}
      opciones={OPCIONES}
      ayuda={AYUDA_DE_CANCELACION}
      mensajeSinOpcion={MENSAJE_ELEGI_QUIEN_PIDIO}
      textoDelBoton="Cancelar turno"
      claseDelBoton="boton-destructivo"
      enviando={enviando}
      error={error}
      onConfirmar={onCancelarTurno}
      onVolver={onVolver}
    />
  )
}
