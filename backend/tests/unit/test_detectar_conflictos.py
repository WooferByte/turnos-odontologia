"""Reglas puras de solapamiento, sin base de datos (E2..E7, D8)."""
from datetime import datetime

from app.domain.agenda.intervalo import Intervalo
from app.domain.agenda.solapamiento import TurnoOcupado, detectar_conflictos
from app.domain.errors import Conflicto
from app.domain.tiempo import UTC
from app.domain.turnos.estados import EstadoTurno


def _intervalo(hora_inicio: int, minuto_inicio: int, hora_fin: int, minuto_fin: int) -> Intervalo:
    return Intervalo(
        datetime(2026, 11, 2, hora_inicio, minuto_inicio, tzinfo=UTC),
        datetime(2026, 11, 2, hora_fin, minuto_fin, tzinfo=UTC),
    )


def test_e2_conflicto_solo_de_profesional():
    existente = TurnoOcupado(7, _intervalo(10, 0, 10, 30), EstadoTurno.RESERVADO)

    conflictos = detectar_conflictos(
        candidato=_intervalo(10, 15, 10, 45),
        profesional_id=1,
        ocupados_profesional=[existente],
        sillon_id=2,
        ocupados_sillon=[],
    )

    assert conflictos == (
        Conflicto(codigo="RN-AG-05", recurso="profesional", recurso_id=1, turno_id=7),
    )
