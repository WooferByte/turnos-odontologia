"""Reglas puras de la cancelación de un turno (CAN-1c, CAN-2a; RN-AG-12, RN-AG-11; design X3 y X7)."""
import pytest

from app.domain.errors import TransicionInvalida
from app.domain.turnos.cancelacion import ESTADOS_DE_CANCELACION, exigir_cancelable
from app.domain.turnos.estados import ESTADOS_ACTIVOS, EstadoTurno
from app.domain.turnos.eventos import Actor, ActorTipo, TipoEvento, evento_cancelado
from tests.conftest import RELOJ_FIJO
from tests.unit.test_eventos import un_turno_de_dominio

ACTOR = Actor(ActorTipo.USUARIO, "2")
TERMINALES = [
    EstadoTurno.CANCELADO_PACIENTE,
    EstadoTurno.CANCELADO_PROFESIONAL,
    EstadoTurno.VENCIDO,
    EstadoTurno.ATENDIDO,
    EstadoTurno.AUSENTE,
]


def test_can1c_un_turno_terminal_no_se_cancela():
    with pytest.raises(TransicionInvalida) as error:
        exigir_cancelable(EstadoTurno.ATENDIDO)

    assert error.value.codigo == "RN-AG-12"
    assert error.value.codigos == ["RN-AG-12"]


def test_can2a_el_evento_cancelado_lleva_el_estado_de_antes_y_de_despues():
    antes = un_turno_de_dominio(estado=EstadoTurno.CONFIRMADO)
    despues = un_turno_de_dominio(estado=EstadoTurno.CANCELADO_PACIENTE)

    evento = evento_cancelado(antes, despues, ACTOR, RELOJ_FIJO)

    assert evento.turno_id == 7
    assert evento.tipo is TipoEvento.CANCELADO
    assert evento.tipo.value == "cancelado"
    assert evento.actor_tipo is ActorTipo.USUARIO
    assert evento.actor_id == "2"
    assert evento.ocurrido_en == RELOJ_FIJO
    assert evento.antes == {"estado": "confirmado"}
    assert evento.despues == {"estado": "cancelado_paciente"}
    assert evento.motivo is None
    assert evento.id is None


@pytest.mark.parametrize("estado", TERMINALES)
def test_can1c_los_cinco_estados_terminales_se_rechazan(estado):
    with pytest.raises(TransicionInvalida):
        exigir_cancelable(estado)


@pytest.mark.parametrize("estado", sorted(ESTADOS_ACTIVOS))
def test_can1b_los_cuatro_estados_activos_se_aceptan(estado):
    assert exigir_cancelable(estado) is None


def test_x3_solo_dos_estados_de_cancelacion():
    assert ESTADOS_DE_CANCELACION == {EstadoTurno.CANCELADO_PACIENTE, EstadoTurno.CANCELADO_PROFESIONAL}
    assert ESTADOS_DE_CANCELACION.isdisjoint(ESTADOS_ACTIVOS)


def test_can2a_el_evento_toma_el_estado_y_el_instante_que_se_le_dan():
    antes = un_turno_de_dominio(id=12, estado=EstadoTurno.PENDIENTE_SENA)
    despues = un_turno_de_dominio(id=12, estado=EstadoTurno.CANCELADO_PROFESIONAL)

    evento = evento_cancelado(antes, despues, Actor(ActorTipo.USUARIO, "9"), RELOJ_FIJO)

    assert evento.turno_id == 12
    assert evento.actor_id == "9"
    assert evento.antes == {"estado": "pendiente_sena"}
    assert evento.despues == {"estado": "cancelado_profesional"}


def test_x7_el_evento_no_se_arma_sin_id():
    con_id = un_turno_de_dominio()
    sin_id = un_turno_de_dominio(id=None)

    with pytest.raises(ValueError):
        evento_cancelado(sin_id, con_id, ACTOR, RELOJ_FIJO)
    with pytest.raises(ValueError):
        evento_cancelado(con_id, sin_id, ACTOR, RELOJ_FIJO)
