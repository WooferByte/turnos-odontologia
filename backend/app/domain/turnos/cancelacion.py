"""Reglas puras de la cancelación de un turno (RN-AG-12, RN-AG-10; D345). Solo biblioteca estándar."""
from app.domain.errors import TransicionInvalida
from app.domain.turnos.estados import ESTADOS_ACTIVOS, EstadoTurno

# Los dos estados a los que lleva cancelar: quién lo pidió (design X3). No es una tabla general de transiciones.
ESTADOS_DE_CANCELACION = frozenset({EstadoTurno.CANCELADO_PACIENTE, EstadoTurno.CANCELADO_PROFESIONAL})


def exigir_cancelable(estado: EstadoTurno) -> None:
    """Solo un turno activo se cancela; uno terminal da ``RN-AG-12``, también si repite la cancelación."""
    if estado not in ESTADOS_ACTIVOS:
        raise TransicionInvalida()
