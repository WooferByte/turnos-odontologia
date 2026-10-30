"""Reglas puras del marcado de asistencia de un turno (RN-AG-12, RN-AG-13, RN-TD-05; design W3, W4, W8). Solo biblioteca estándar."""
from datetime import datetime

from app.domain.errors import MarcadoAntesDelInicio, TransicionInvalida
from app.domain.turnos.estados import EstadoTurno

# A qué estados lleva marcar y desde cuáles se puede (design W3). No es una tabla general de transiciones.
ESTADOS_DE_ASISTENCIA = frozenset({EstadoTurno.ATENDIDO, EstadoTurno.AUSENTE})
ESTADOS_QUE_SE_MARCAN = frozenset({EstadoTurno.RESERVADO, EstadoTurno.CONFIRMADO})


def exigir_marcable(estado: EstadoTurno, inicio: datetime, ahora: datetime) -> None:
    """Primero el estado (``RN-AG-12``) y, si se marca, el momento (``RN-AG-13``): ``ahora == inicio`` se admite."""
    if estado not in ESTADOS_QUE_SE_MARCAN:
        raise TransicionInvalida()
    if ahora < inicio:
        raise MarcadoAntesDelInicio()


def deja_de_ser_nuevo(estado_nuevo: EstadoTurno) -> bool:
    """El paciente deja de ser nuevo solo con un turno ``atendido`` (RN-TD-05, D52); ``ausente`` no cuenta."""
    return estado_nuevo is EstadoTurno.ATENDIDO
