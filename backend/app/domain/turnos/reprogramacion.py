"""Reglas puras de la reprogramación de un turno (RN-AG-18, RN-AG-01; D333, D334). Solo biblioteca estándar."""
from app.domain.agenda.prestaciones import GRANULARIDAD_MINUTOS, duracion_valida
from app.domain.errors import DuracionInvalida, TurnoNoReprogramable
from app.domain.turnos.estados import ESTADOS_ACTIVOS, EstadoTurno

DURACION_MAXIMA_DEL_TURNO_MINUTOS = 1440  # 24 horas (D333); las prestaciones no tienen tope todavía


def exigir_reprogramable(estado: EstadoTurno) -> None:
    """Solo un turno activo se reprograma; uno terminal da ``RN-AG-18`` (D334)."""
    if estado not in ESTADOS_ACTIVOS:
        raise TurnoNoReprogramable()


def exigir_duracion_del_turno(minutos: int) -> None:
    """Mayor que 0, múltiplo de la granularidad y hasta 1440 minutos (RN-AG-01, D333)."""
    if not duracion_valida(minutos) or minutos > DURACION_MAXIMA_DEL_TURNO_MINUTOS:
        raise DuracionInvalida(GRANULARIDAD_MINUTOS)
