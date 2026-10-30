// Panel lateral «Registrar asistencia» (design W12, W13): pregunta cómo terminó el turno, sin opción marcada, y manda
// el estado elegido. No evalúa reglas: las decide la API (tampoco compara la hora del turno con el reloj).
import { IconoAsistencia } from '../../shared/iconos/IconoAsistencia'
import type { EstadoDeAsistencia, TurnoDeLaAgenda } from './apiAgenda'
import {
  ACCION_REGISTRAR_ASISTENCIA,
  AYUDA_DE_CANCELACION,
  MENSAJE_ELEGI_COMO_TERMINO,
  OPCION_ATENDIDO,
  OPCION_AUSENTE,
  PREGUNTA_DE_ASISTENCIA,
} from './mensajes'
import { PanelDeDecision, type OpcionDeDecision } from './PanelDeDecision'

interface Propiedades {
  turno: TurnoDeLaAgenda
  zonaHoraria: string
  enviando: boolean
  /** Rechazo de la API ya traducido a su texto fijo; `null` si no hay. */
  error: string | null
  onRegistrar(estado: EstadoDeAsistencia): void
  /** Cierra el panel sin pedir nada («Volver» y «Cerrar»). */
  onVolver(): void
}

const OPCIONES: readonly OpcionDeDecision<EstadoDeAsistencia>[] = [
  { estado: 'atendido', texto: OPCION_ATENDIDO },
  { estado: 'ausente', texto: OPCION_AUSENTE },
]

export function PanelAsistencia({ turno, zonaHoraria, enviando, error, onRegistrar, onVolver }: Propiedades) {
  return (
    <PanelDeDecision
      clase="panel-de-asistencia"
      titulo={ACCION_REGISTRAR_ASISTENCIA}
      icono={<IconoAsistencia />}
      turno={turno}
      zonaHoraria={zonaHoraria}
      pregunta={PREGUNTA_DE_ASISTENCIA}
      opciones={OPCIONES}
      ayuda={AYUDA_DE_CANCELACION}
      mensajeSinOpcion={MENSAJE_ELEGI_COMO_TERMINO}
      textoDelBoton={ACCION_REGISTRAR_ASISTENCIA}
      claseDelBoton="boton-primario"
      enviando={enviando}
      error={error}
      onConfirmar={onRegistrar}
      onVolver={onVolver}
    />
  )
}
