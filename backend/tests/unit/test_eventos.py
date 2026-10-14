"""Evento ``creado`` del historial como tipo de dominio (E9; RN-AG-11, design H3 y H5)."""
from datetime import datetime, timezone

from app.domain.tiempo import a_texto_utc
from app.domain.turnos.estados import EstadoTurno
from app.domain.turnos.eventos import (
    ACTOR_PANEL_SIN_AUTENTICAR,
    ActorTipo,
    TipoEvento,
    evento_creado,
)
from app.domain.turnos.turno import Turno
from tests.conftest import RELOJ_FIJO, a_las


def un_turno_de_dominio(**kw) -> Turno:
    datos = {
        "id": 7,
        "consultorio_id": 1,
        "paciente_id": 3,
        "profesional_id": 2,
        "sillon_id": 4,
        "prestacion_id": 5,
        "inicio": a_las(10),
        "fin": a_las(10, 30),
        "duracion_minutos": 30,
        "estado": EstadoTurno.RESERVADO,
        "creado_en": RELOJ_FIJO,
    }
    return Turno(**{**datos, **kw})


def test_e9_evento_creado_toma_los_datos_del_turno():
    turno = un_turno_de_dominio()

    evento = evento_creado(turno, ACTOR_PANEL_SIN_AUTENTICAR)

    assert evento.turno_id == 7
    assert evento.tipo is TipoEvento.CREADO
    assert evento.actor_tipo is ActorTipo.USUARIO
    assert evento.actor_id is None
    assert evento.ocurrido_en == turno.creado_en
    assert evento.antes is None
    assert evento.motivo is None
    assert evento.id is None
    assert evento.despues == {
        "estado": "reservado",
        "inicio": "2026-11-02T10:00:00Z",
        "fin": "2026-11-02T10:30:00Z",
        "duracion_minutos": 30,
        "paciente_id": 3,
        "prestacion_id": 5,
        "profesional_id": 2,
        "sillon_id": 4,
    }


def test_a_texto_utc_escribe_la_fecha_con_z():
    assert a_texto_utc(datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc)) == "2026-11-02T10:00:00Z"
