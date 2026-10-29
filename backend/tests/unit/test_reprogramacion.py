"""Reglas puras de la reprogramación, sin base de datos (REP-5a, REP-2a, REP-3c; RN-AG-18, RN-AG-11, RN-AG-01)."""
from datetime import timedelta

import pytest

from app.domain.errors import DuracionInvalida, TurnoNoReprogramable
from app.domain.tiempo import UTC
from app.domain.turnos.estados import ESTADOS_ACTIVOS, EstadoTurno
from app.domain.turnos.eventos import Actor, ActorTipo, TipoEvento, evento_reprogramado
from app.domain.turnos.reprogramacion import (
    DURACION_MAXIMA_DEL_TURNO_MINUTOS,
    exigir_duracion_del_turno,
    exigir_reprogramable,
)
from tests.conftest import RELOJ_FIJO, a_las
from tests.unit.test_eventos import un_turno_de_dominio

ACTOR = Actor(ActorTipo.USUARIO, "2")
TERMINALES = [
    EstadoTurno.CANCELADO_PACIENTE,
    EstadoTurno.CANCELADO_PROFESIONAL,
    EstadoTurno.VENCIDO,
    EstadoTurno.ATENDIDO,
    EstadoTurno.AUSENTE,
]


def test_rep5a_un_turno_terminal_no_se_reprograma():
    with pytest.raises(TurnoNoReprogramable) as error:
        exigir_reprogramable(EstadoTurno.CANCELADO_PACIENTE)

    assert error.value.codigo == "RN-AG-18"
    assert error.value.codigos == ["RN-AG-18"]


@pytest.mark.parametrize("estado", TERMINALES)
def test_rep5a_los_cinco_estados_terminales_se_rechazan(estado):
    with pytest.raises(TurnoNoReprogramable):
        exigir_reprogramable(estado)


@pytest.mark.parametrize("estado", sorted(ESTADOS_ACTIVOS))
def test_rep5a_los_cuatro_estados_activos_se_aceptan(estado):
    assert exigir_reprogramable(estado) is None


def test_rep2a_el_evento_reprogramado_lleva_antes_y_despues():
    antes = un_turno_de_dominio(inicio=a_las(13), fin=a_las(13, 30), duracion_minutos=30)
    despues = un_turno_de_dominio(inicio=a_las(17), fin=a_las(17, 45), duracion_minutos=45)

    evento = evento_reprogramado(antes, despues, ACTOR, RELOJ_FIJO)

    assert evento.turno_id == 7
    assert evento.tipo is TipoEvento.REPROGRAMADO
    assert evento.tipo.value == "reprogramado"
    assert evento.actor_tipo is ActorTipo.USUARIO
    assert evento.actor_id == "2"
    assert evento.ocurrido_en == RELOJ_FIJO
    assert evento.motivo is None
    assert evento.id is None
    assert evento.antes == {
        "inicio": "2026-11-02T13:00:00Z",
        "fin": "2026-11-02T13:30:00Z",
        "duracion_minutos": 30,
    }
    assert evento.despues == {
        "inicio": "2026-11-02T17:00:00Z",
        "fin": "2026-11-02T17:45:00Z",
        "duracion_minutos": 45,
    }


def test_rep2a_el_evento_cruza_el_dia_en_utc_con_z():
    antes = un_turno_de_dominio(id=12, inicio=a_las(9), fin=a_las(9, 30), duracion_minutos=30)
    despues = un_turno_de_dominio(
        id=12,
        inicio=a_las(23, 30),
        fin=a_las(23, 30) + timedelta(minutes=45),
        duracion_minutos=45,
    )

    evento = evento_reprogramado(antes, despues, Actor(ActorTipo.USUARIO, "9"), a_las(12))

    assert evento.turno_id == 12
    assert evento.actor_id == "9"
    assert evento.ocurrido_en == a_las(12)
    assert evento.despues == {
        "inicio": "2026-11-02T23:30:00Z",
        "fin": "2026-11-03T00:15:00Z",
        "duracion_minutos": 45,
    }


def test_m8_el_evento_no_se_arma_sin_id():
    con_id = un_turno_de_dominio()
    sin_id = un_turno_de_dominio(id=None)

    with pytest.raises(ValueError):
        evento_reprogramado(sin_id, con_id, ACTOR, RELOJ_FIJO)
    with pytest.raises(ValueError):
        evento_reprogramado(con_id, sin_id, ACTOR, RELOJ_FIJO)


@pytest.mark.parametrize("minutos", [1445, 1500, 1_000_000_000])
def test_rep3c_la_duracion_del_turno_tiene_tope(minutos):
    with pytest.raises(DuracionInvalida) as error:
        exigir_duracion_del_turno(minutos)

    assert error.value.codigo == "RN-AG-01"
    assert error.value.campo == "duracion_minutos"


@pytest.mark.parametrize("minutos", [42, 0, -5, 1441])
def test_rep3b_la_duracion_del_turno_sigue_siendo_multiplo_de_5_y_positiva(minutos):
    with pytest.raises(DuracionInvalida):
        exigir_duracion_del_turno(minutos)


@pytest.mark.parametrize("minutos", [5, 30, 1435, 1440])
def test_rep3c_las_duraciones_validas_pasan_incluido_el_tope(minutos):
    assert exigir_duracion_del_turno(minutos) is None


def test_rep3c_el_tope_es_de_24_horas():
    assert DURACION_MAXIMA_DEL_TURNO_MINUTOS == 1440
