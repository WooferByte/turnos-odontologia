"""Evento ``creado`` del historial como tipo de dominio (E9; RN-AG-11, design H3 y H5)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.domain.errors import FechaNoUTC
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


@pytest.mark.parametrize(
    ("turno", "inicio_esperado", "fin_esperado"),
    [
        (un_turno_de_dominio(), "2026-11-02T10:00:00Z", "2026-11-02T10:30:00Z"),
        (
            un_turno_de_dominio(
                id=12,
                paciente_id=9,
                profesional_id=6,
                sillon_id=8,
                prestacion_id=11,
                inicio=a_las(23, 30),
                fin=a_las(23, 30) + timedelta(minutes=45),
                duracion_minutos=45,
            ),
            "2026-11-02T23:30:00Z",
            "2026-11-03T00:15:00Z",
        ),
    ],
)
def test_e9_evento_creado_toma_los_datos_del_turno(turno, inicio_esperado, fin_esperado):
    evento = evento_creado(turno, ACTOR_PANEL_SIN_AUTENTICAR)

    assert evento.turno_id == turno.id
    assert evento.tipo is TipoEvento.CREADO
    assert evento.actor_tipo is ActorTipo.USUARIO
    assert evento.actor_id is None
    assert evento.ocurrido_en == turno.creado_en
    assert evento.antes is None
    assert evento.motivo is None
    assert evento.id is None
    assert evento.despues == {
        "estado": "reservado",
        "inicio": inicio_esperado,
        "fin": fin_esperado,
        "duracion_minutos": turno.duracion_minutos,
        "paciente_id": turno.paciente_id,
        "prestacion_id": turno.prestacion_id,
        "profesional_id": turno.profesional_id,
        "sillon_id": turno.sillon_id,
    }


def test_evento_creado_exige_un_turno_guardado():
    with pytest.raises(ValueError):
        evento_creado(un_turno_de_dominio(id=None), ACTOR_PANEL_SIN_AUTENTICAR)


@pytest.mark.parametrize(
    ("fecha", "texto"),
    [
        (datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc), "2026-11-02T10:00:00Z"),
        (datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc), "2026-12-31T23:59:59Z"),
    ],
)
def test_a_texto_utc_escribe_la_fecha_con_z(fecha, texto):
    assert a_texto_utc(fecha) == texto


def test_a_texto_utc_rechaza_una_fecha_sin_zona():
    with pytest.raises(FechaNoUTC) as info:
        a_texto_utc(datetime(2026, 11, 2, 10, 0))

    assert info.value.codigos == ["RN-GL-01"]
