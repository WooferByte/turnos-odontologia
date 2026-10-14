"""Historial de turnos: E9, el evento ``creado`` lo registra ``crear_turno`` (RN-AG-11, design H8)."""
from dataclasses import replace

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError

from app.application.crear_turno import CrearTurnoComando, crear_turno
from app.application.historial import consultar_historial
from app.domain.errors import (
    EntradaInvalida,
    ErrorDeSolapamiento,
    ReferenciaInvalida,
    TurnoNoEncontrado,
)
from app.domain.turnos.eventos import ActorTipo, TipoEvento
from app.infrastructure.db.modelos import EventoTurnoModelo, TurnoModelo
from app.infrastructure.repositories.historial import RepositorioHistorialSqlAlchemy
from tests.conftest import RELOJ_FIJO, a_las, reloj_fijo
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
)


def _escenario(sesion, duracion_minutos: int = 30) -> dict:
    consultorio = un_consultorio(sesion)
    return {
        "consultorio": consultorio,
        "paciente": un_paciente(sesion, consultorio),
        "profesional": un_profesional(sesion, consultorio),
        "sillon": un_sillon(sesion, consultorio),
        "prestacion": una_prestacion(sesion, consultorio, duracion_minutos=duracion_minutos),
    }


def _comando(datos: dict, inicio) -> CrearTurnoComando:
    return CrearTurnoComando(
        paciente_id=datos["paciente"].id,
        prestacion_id=datos["prestacion"].id,
        inicio=inicio,
        profesional_id=datos["profesional"].id,
        sillon_id=datos["sillon"].id,
    )


def test_e9_crear_turno_registra_el_evento_creado(sesion, fabrica_sesiones, uow):
    datos = _escenario(sesion)

    turno = crear_turno(_comando(datos, a_las(10)), uow, reloj_fijo)

    with fabrica_sesiones() as otra_sesion:  # sesión nueva: lo que quedó confirmado en la base
        eventos = RepositorioHistorialSqlAlchemy(otra_sesion).del_turno(turno.id)
    assert len(eventos) == 1
    evento = eventos[0]
    assert evento.turno_id == turno.id
    assert evento.tipo is TipoEvento.CREADO
    assert evento.ocurrido_en == RELOJ_FIJO == turno.creado_en
    assert evento.actor_tipo is ActorTipo.USUARIO
    assert evento.actor_id is None
    assert evento.antes is None
    assert evento.motivo is None
    assert evento.despues == {
        "estado": "reservado",
        "inicio": "2026-11-02T10:00:00Z",
        "fin": "2026-11-02T10:30:00Z",
        "duracion_minutos": 30,
        "paciente_id": datos["paciente"].id,
        "prestacion_id": datos["prestacion"].id,
        "profesional_id": datos["profesional"].id,
        "sillon_id": datos["sillon"].id,
    }


def _cantidad(fabrica_sesiones, modelo) -> int:
    with fabrica_sesiones() as lectura:
        return lectura.scalar(select(func.count()).select_from(modelo))


@pytest.mark.parametrize(
    ("inicio", "prestacion_inexistente", "excepcion"),
    [
        pytest.param(a_las(10), False, ErrorDeSolapamiento, id="solapamiento_409"),
        pytest.param(a_las(15), True, EntradaInvalida, id="referencia_invalida_422"),
    ],
)
def test_e9_un_rechazo_no_registra_ningun_evento(
    sesion, fabrica_sesiones, uow, inicio, prestacion_inexistente, excepcion
):
    datos = _escenario(sesion)
    crear_turno(_comando(datos, a_las(10)), uow, reloj_fijo)  # el turno existente, con su evento
    pedido = _comando(datos, inicio)
    if prestacion_inexistente:
        pedido = replace(pedido, prestacion_id=999)

    with pytest.raises(excepcion):
        crear_turno(pedido, uow, reloj_fijo)

    assert _cantidad(fabrica_sesiones, EventoTurnoModelo) == 1
    assert _cantidad(fabrica_sesiones, TurnoModelo) == 1


def test_e9_si_el_evento_no_se_guarda_no_queda_el_turno(sesion, engine, fabrica_sesiones, uow):
    datos = _escenario(sesion)
    with engine.begin() as conexion:  # falla real de la base, sin dobles (design H15, V2)
        conexion.exec_driver_sql(
            "CREATE TRIGGER evento_turno_falla BEFORE INSERT ON evento_turno "
            "BEGIN SELECT RAISE(ABORT, 'falla de prueba al registrar el evento'); END"
        )

    with pytest.raises(DBAPIError, match="falla de prueba al registrar el evento"):
        crear_turno(_comando(datos, a_las(10)), uow, reloj_fijo)

    assert _cantidad(fabrica_sesiones, TurnoModelo) == 0
    assert _cantidad(fabrica_sesiones, EventoTurnoModelo) == 0


def test_ca1_consultar_historial_devuelve_los_eventos_del_turno(sesion, uow):
    datos = _escenario(sesion)
    turno = crear_turno(_comando(datos, a_las(10)), uow, reloj_fijo)

    eventos = consultar_historial(turno.id, uow)

    assert len(eventos) == 1
    assert eventos[0].turno_id == turno.id
    assert eventos[0].tipo is TipoEvento.CREADO
    assert eventos[0].actor_tipo is ActorTipo.USUARIO
    assert eventos[0].ocurrido_en == RELOJ_FIJO


def test_his1_turno_inexistente_rechaza_con_rn_gl_04(uow):
    with pytest.raises(TurnoNoEncontrado) as excinfo:
        consultar_historial(999, uow)

    assert excinfo.value.codigos == ["RN-GL-04"]
    assert excinfo.value.referencias == (ReferenciaInvalida("turno", 999, "inexistente"),)
