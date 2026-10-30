"""Reglas puras del marcado de asistencia (ASI-1, ASI-2a, ASI-3; RN-AG-12, RN-AG-13, RN-AG-11, RN-TD-05; design W3, W4, W7)."""
from datetime import timedelta

import pytest

from app.domain.errors import MarcadoAntesDelInicio, TransicionInvalida
from app.domain.turnos.asistencia import (
    ESTADOS_DE_ASISTENCIA,
    ESTADOS_QUE_SE_MARCAN,
    deja_de_ser_nuevo,
    exigir_marcable,
)
from app.domain.turnos.estados import ESTADOS_ACTIVOS, EstadoTurno
from app.domain.turnos.eventos import Actor, ActorTipo, TipoEvento, evento_estado_cambiado
from tests.conftest import RELOJ_FIJO, a_las
from tests.unit.test_eventos import un_turno_de_dominio

ACTOR = Actor(ActorTipo.USUARIO, "2")
INICIO = a_las(13)
NO_SE_MARCAN = [
    EstadoTurno.PENDIENTE_APROBACION,
    EstadoTurno.PENDIENTE_SENA,
    EstadoTurno.CANCELADO_PACIENTE,
    EstadoTurno.CANCELADO_PROFESIONAL,
    EstadoTurno.VENCIDO,
    EstadoTurno.ATENDIDO,
    EstadoTurno.AUSENTE,
]


def test_asi1c_un_turno_cancelado_no_se_marca():
    with pytest.raises(TransicionInvalida) as error:
        exigir_marcable(EstadoTurno.CANCELADO_PACIENTE, INICIO, INICIO + timedelta(hours=1))

    assert error.value.codigo == "RN-AG-12"
    assert error.value.codigos == ["RN-AG-12"]


def test_asi1d_antes_del_inicio_da_rn_ag_13():
    with pytest.raises(MarcadoAntesDelInicio) as error:
        exigir_marcable(EstadoTurno.RESERVADO, INICIO, INICIO - timedelta(seconds=1))

    assert error.value.codigo == "RN-AG-13"
    assert error.value.codigos == ["RN-AG-13"]


def test_asi3a_atendido_deja_de_ser_nuevo():
    assert deja_de_ser_nuevo(EstadoTurno.ATENDIDO) is True


def test_asi2a_el_evento_estado_cambiado_lleva_el_estado_de_antes_y_de_despues():
    antes = un_turno_de_dominio(estado=EstadoTurno.CONFIRMADO)
    despues = un_turno_de_dominio(estado=EstadoTurno.ATENDIDO)

    evento = evento_estado_cambiado(antes, despues, ACTOR, RELOJ_FIJO)

    assert evento.turno_id == 7
    assert evento.tipo is TipoEvento.ESTADO_CAMBIADO
    assert evento.tipo.value == "estado_cambiado"
    assert evento.actor_tipo is ActorTipo.USUARIO
    assert evento.actor_id == "2"
    assert evento.ocurrido_en == RELOJ_FIJO
    assert evento.antes == {"estado": "confirmado"}
    assert evento.despues == {"estado": "atendido"}
    assert evento.motivo is None
    assert evento.id is None


@pytest.mark.parametrize("estado", NO_SE_MARCAN)
def test_asi1c_los_siete_estados_que_no_se_marcan_dan_rn_ag_12(estado):
    with pytest.raises(TransicionInvalida):
        exigir_marcable(estado, INICIO, INICIO + timedelta(hours=1))


@pytest.mark.parametrize("estado", [EstadoTurno.RESERVADO, EstadoTurno.CONFIRMADO])
def test_asi1a_reservado_y_confirmado_se_marcan(estado):
    assert exigir_marcable(estado, INICIO, INICIO + timedelta(hours=1)) is None


@pytest.mark.parametrize("estado", [EstadoTurno.RESERVADO, EstadoTurno.CONFIRMADO])
def test_asi1b_ahora_igual_a_inicio_se_admite(estado):
    assert exigir_marcable(estado, INICIO, INICIO) is None


@pytest.mark.parametrize("estado", [EstadoTurno.RESERVADO, EstadoTurno.CONFIRMADO])
def test_asi1d_un_segundo_antes_se_rechaza_para_los_dos_estados(estado):
    with pytest.raises(MarcadoAntesDelInicio):
        exigir_marcable(estado, INICIO, INICIO - timedelta(seconds=1))


def test_asi1d_el_estado_se_evalua_antes_que_el_momento():
    with pytest.raises(TransicionInvalida):
        exigir_marcable(EstadoTurno.CANCELADO_PACIENTE, INICIO, INICIO - timedelta(days=1))


def test_asi3b_ausente_no_deja_de_ser_nuevo():
    assert deja_de_ser_nuevo(EstadoTurno.AUSENTE) is False


def test_w3_solo_dos_estados_de_asistencia():
    assert ESTADOS_DE_ASISTENCIA == {EstadoTurno.ATENDIDO, EstadoTurno.AUSENTE}
    assert ESTADOS_DE_ASISTENCIA.isdisjoint(ESTADOS_ACTIVOS)
    assert ESTADOS_QUE_SE_MARCAN == {EstadoTurno.RESERVADO, EstadoTurno.CONFIRMADO}


def test_w7_el_evento_no_se_arma_sin_id():
    sin_id = un_turno_de_dominio(id=None)
    con_id = un_turno_de_dominio(estado=EstadoTurno.ATENDIDO)

    with pytest.raises(ValueError):
        evento_estado_cambiado(sin_id, con_id, ACTOR, RELOJ_FIJO)
    with pytest.raises(ValueError):
        evento_estado_cambiado(con_id, sin_id, ACTOR, RELOJ_FIJO)
