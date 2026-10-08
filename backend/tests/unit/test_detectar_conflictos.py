"""Reglas puras de solapamiento, sin base de datos (E2..E7, D8)."""
from app.domain.agenda.intervalo import Intervalo
from app.domain.agenda.solapamiento import TurnoOcupado, detectar_conflictos
from app.domain.errors import Conflicto
from app.domain.turnos.estados import EstadoTurno
from tests.conftest import a_las


def test_e2_conflicto_solo_de_profesional():
    existente = TurnoOcupado(7, Intervalo(a_las(10), a_las(10, 30)), EstadoTurno.RESERVADO)

    conflictos = detectar_conflictos(
        candidato=Intervalo(a_las(10, 15), a_las(10, 45)),
        profesional_id=1,
        ocupados_profesional=[existente],
        sillon_id=2,
        ocupados_sillon=[],
    )

    assert conflictos == (
        Conflicto(codigo="RN-AG-05", recurso="profesional", recurso_id=1, turno_id=7),
    )
