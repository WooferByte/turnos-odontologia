"""Caso de uso: consultar el historial de un turno (US-015 CA-1, HIS-1). Solo lee."""
from collections.abc import Sequence

from app.application.puertos import UnidadDeTrabajo
from app.domain.errors import TurnoNoEncontrado
from app.domain.turnos.eventos import EventoTurno


def consultar_historial(turno_id: int, uow: UnidadDeTrabajo) -> Sequence[EventoTurno]:
    """Eventos del turno en orden cronológico; un turno sin eventos da una lista vacía (H14)."""
    with uow:
        if not uow.agenda.existe_turno(turno_id):
            raise TurnoNoEncontrado(turno_id)
        return uow.historial.del_turno(turno_id)
