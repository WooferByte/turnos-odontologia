"""Reglas puras de solapamiento, sin base de datos (E2..E7, D8)."""
import pytest

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


@pytest.mark.parametrize(
    "estado",
    [
        EstadoTurno.CANCELADO_PACIENTE,
        EstadoTurno.CANCELADO_PROFESIONAL,
        EstadoTurno.VENCIDO,
        EstadoTurno.ATENDIDO,
        EstadoTurno.AUSENTE,
    ],
    ids=lambda estado: estado.value,
)
def test_e6_estados_no_activos_no_generan_conflicto(estado):
    # Un turno en estado no activo libera el horario (RN-AG-10), sea del profesional o del sillón.
    existente_del_profesional = TurnoOcupado(7, Intervalo(a_las(10), a_las(10, 30)), estado)
    existente_del_sillon = TurnoOcupado(8, Intervalo(a_las(10), a_las(10, 30)), estado)

    conflictos = detectar_conflictos(
        candidato=Intervalo(a_las(10), a_las(10, 30)),
        profesional_id=1,
        ocupados_profesional=[existente_del_profesional],
        sillon_id=2,
        ocupados_sillon=[existente_del_sillon],
    )

    assert conflictos == ()


@pytest.mark.parametrize(
    "estado",
    [
        EstadoTurno.PENDIENTE_APROBACION,
        EstadoTurno.PENDIENTE_SENA,
        EstadoTurno.RESERVADO,
        EstadoTurno.CONFIRMADO,
    ],
    ids=lambda estado: estado.value,
)
def test_e6_estados_activos_si_generan_conflicto(estado):
    existente_del_profesional = TurnoOcupado(7, Intervalo(a_las(10), a_las(10, 30)), estado)
    existente_del_sillon = TurnoOcupado(8, Intervalo(a_las(10), a_las(10, 30)), estado)

    conflictos = detectar_conflictos(
        candidato=Intervalo(a_las(10), a_las(10, 30)),
        profesional_id=1,
        ocupados_profesional=[existente_del_profesional],
        sillon_id=2,
        ocupados_sillon=[existente_del_sillon],
    )

    assert conflictos == (
        Conflicto(codigo="RN-AG-05", recurso="profesional", recurso_id=1, turno_id=7),
        Conflicto(codigo="RN-AG-08", recurso="sillon", recurso_id=2, turno_id=8),
    )


def test_rep1b_el_turno_no_choca_consigo_mismo():
    propio = TurnoOcupado(7, Intervalo(a_las(13), a_las(13, 30)), EstadoTurno.RESERVADO)

    conflictos = detectar_conflictos(
        candidato=Intervalo(a_las(13, 15), a_las(13, 45)),
        profesional_id=1,
        ocupados_profesional=[propio],
        sillon_id=2,
        ocupados_sillon=[propio],
        excluir_turno_id=7,
    )

    assert conflictos == ()


def test_rep1b_excluir_un_turno_no_excluye_a_los_demas():
    propio = TurnoOcupado(7, Intervalo(a_las(13), a_las(13, 30)), EstadoTurno.RESERVADO)
    otro = TurnoOcupado(8, Intervalo(a_las(13, 30), a_las(14)), EstadoTurno.CONFIRMADO)

    conflictos = detectar_conflictos(
        candidato=Intervalo(a_las(13, 15), a_las(13, 45)),
        profesional_id=1,
        ocupados_profesional=[propio, otro],
        sillon_id=2,
        ocupados_sillon=[propio, otro],
        excluir_turno_id=7,
    )

    assert conflictos == (
        Conflicto(codigo="RN-AG-05", recurso="profesional", recurso_id=1, turno_id=8),
        Conflicto(codigo="RN-AG-08", recurso="sillon", recurso_id=2, turno_id=8),
    )


@pytest.mark.parametrize("excluir_turno_id", [None, 99])
def test_rep1b_sin_excluir_o_excluyendo_otro_id_el_propio_turno_choca(excluir_turno_id):
    propio = TurnoOcupado(7, Intervalo(a_las(13), a_las(13, 30)), EstadoTurno.RESERVADO)

    conflictos = detectar_conflictos(
        Intervalo(a_las(13, 15), a_las(13, 45)),
        1,
        [propio],
        2,
        [],
        excluir_turno_id=excluir_turno_id,
    )

    assert conflictos == (
        Conflicto(codigo="RN-AG-05", recurso="profesional", recurso_id=1, turno_id=7),
    )


def test_rep1b_el_comportamiento_de_siempre_no_cambia_sin_el_parametro():
    propio = TurnoOcupado(7, Intervalo(a_las(13), a_las(13, 30)), EstadoTurno.RESERVADO)

    conflictos = detectar_conflictos(Intervalo(a_las(13, 15), a_las(13, 45)), 1, [propio], 2, [])

    assert [c.turno_id for c in conflictos] == [7]
