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


def test_e3_conflicto_solo_de_sillon():
    existente = TurnoOcupado(8, Intervalo(a_las(10), a_las(10, 30)), EstadoTurno.RESERVADO)

    conflictos = detectar_conflictos(
        candidato=Intervalo(a_las(10), a_las(10, 30)),
        profesional_id=2,
        ocupados_profesional=[],
        sillon_id=1,
        ocupados_sillon=[existente],
    )

    assert conflictos == (
        Conflicto(codigo="RN-AG-08", recurso="sillon", recurso_id=1, turno_id=8),
    )


def test_e4_dos_conflictos_profesional_primero():
    del_profesional = TurnoOcupado(7, Intervalo(a_las(10), a_las(10, 30)), EstadoTurno.RESERVADO)
    del_sillon = TurnoOcupado(8, Intervalo(a_las(10, 15), a_las(10, 45)), EstadoTurno.CONFIRMADO)

    conflictos = detectar_conflictos(
        candidato=Intervalo(a_las(10, 10), a_las(10, 40)),
        profesional_id=1,
        ocupados_profesional=[del_profesional],
        sillon_id=2,
        ocupados_sillon=[del_sillon],
    )

    assert conflictos == (
        Conflicto(codigo="RN-AG-05", recurso="profesional", recurso_id=1, turno_id=7),
        Conflicto(codigo="RN-AG-08", recurso="sillon", recurso_id=2, turno_id=8),
    )


def test_conflicto_lleva_el_turno_que_empieza_primero():
    # Dos turnos activos por recurso que chocan con el candidato, entregados en orden inverso.
    temprano_prof = TurnoOcupado(1, Intervalo(a_las(10), a_las(10, 30)), EstadoTurno.RESERVADO)
    tarde_prof = TurnoOcupado(2, Intervalo(a_las(10, 30), a_las(11)), EstadoTurno.RESERVADO)
    temprano_sillon = TurnoOcupado(3, Intervalo(a_las(10), a_las(10, 30)), EstadoTurno.RESERVADO)
    tarde_sillon = TurnoOcupado(4, Intervalo(a_las(10, 30), a_las(11)), EstadoTurno.RESERVADO)

    conflictos = detectar_conflictos(
        candidato=Intervalo(a_las(10), a_las(11)),
        profesional_id=1,
        ocupados_profesional=[tarde_prof, temprano_prof],
        sillon_id=2,
        ocupados_sillon=[tarde_sillon, temprano_sillon],
    )

    assert conflictos == (
        Conflicto(codigo="RN-AG-05", recurso="profesional", recurso_id=1, turno_id=1),
        Conflicto(codigo="RN-AG-08", recurso="sillon", recurso_id=2, turno_id=3),
    )
