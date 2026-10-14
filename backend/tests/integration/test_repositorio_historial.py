"""Repositorio del historial sobre SQLite en memoria (US-015 CA-1; RN-AG-11, design H7)."""
from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.tiempo import UTC
from app.domain.turnos.estados import EstadoTurno
from app.domain.turnos.eventos import ActorTipo, EventoTurno, TipoEvento
from app.domain.turnos.turno import Turno
from app.infrastructure.db.modelos import TurnoModelo
from app.infrastructure.repositories.agenda import RepositorioAgendaSqlAlchemy
from app.infrastructure.repositories.historial import RepositorioHistorialSqlAlchemy
from tests.conftest import RELOJ_FIJO, a_las
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
)


@pytest.fixture
def mundo(sesion: Session) -> dict:
    consultorio = un_consultorio(sesion)
    return {
        "consultorio": consultorio,
        "paciente": un_paciente(sesion, consultorio),
        "prestacion": una_prestacion(sesion, consultorio),
        "profesional": un_profesional(sesion, consultorio),
        "sillon": un_sillon(sesion, consultorio),
    }


def _turno(sesion: Session, mundo: dict, inicio: datetime = a_las(10)) -> TurnoModelo:
    return un_turno(
        sesion,
        paciente=mundo["paciente"],
        profesional=mundo["profesional"],
        sillon=mundo["sillon"],
        prestacion=mundo["prestacion"],
        inicio=inicio,
    )


def _evento(turno_id: int, ocurrido_en: datetime = RELOJ_FIJO, **kw) -> EventoTurno:
    datos = {
        "turno_id": turno_id,
        "tipo": TipoEvento.CREADO,
        "actor_tipo": ActorTipo.USUARIO,
        "actor_id": None,
        "ocurrido_en": ocurrido_en,
        "antes": None,
        "despues": {"estado": "reservado", "duracion_minutos": 30},
        "motivo": None,
    }
    return EventoTurno(**{**datos, **kw})


def test_registrar_devuelve_el_evento_con_id_y_otra_sesion_lo_lee_igual(
    sesion: Session, fabrica_sesiones, mundo: dict
) -> None:
    turno = _turno(sesion, mundo)
    evento = _evento(turno.id, actor_id="u-1", antes={"estado": "reservado"}, motivo="prueba")

    with fabrica_sesiones() as escritura:
        guardado = RepositorioHistorialSqlAlchemy(escritura).registrar(evento)
        escritura.commit()

    assert guardado.id is not None
    with fabrica_sesiones() as lectura:
        leidos = RepositorioHistorialSqlAlchemy(lectura).del_turno(turno.id)
    assert leidos == [guardado]
    assert leidos[0].ocurrido_en.tzinfo is not None
    assert leidos[0].ocurrido_en.utcoffset().total_seconds() == 0
    assert leidos[0].antes == {"estado": "reservado"}
    assert leidos[0].despues == {"estado": "reservado", "duracion_minutos": 30}


def test_ca1_del_turno_ordena_por_ocurrido_en_y_por_registro(sesion: Session, mundo: dict) -> None:
    turno = _turno(sesion, mundo)
    repositorio = RepositorioHistorialSqlAlchemy(sesion)
    primero = repositorio.registrar(_evento(turno.id, datetime(2026, 10, 7, 12, 0, tzinfo=UTC)))
    segundo = repositorio.registrar(_evento(turno.id, datetime(2026, 10, 7, 11, 0, tzinfo=UTC)))
    tercero = repositorio.registrar(_evento(turno.id, datetime(2026, 10, 7, 11, 0, tzinfo=UTC)))
    sesion.commit()

    eventos = repositorio.del_turno(turno.id)

    assert [e.id for e in eventos] == [segundo.id, tercero.id, primero.id]


def test_del_turno_no_trae_eventos_de_otro_turno(sesion: Session, mundo: dict) -> None:
    uno = _turno(sesion, mundo, a_las(10))
    otro = _turno(sesion, mundo, a_las(11))
    repositorio = RepositorioHistorialSqlAlchemy(sesion)
    del_uno = repositorio.registrar(_evento(uno.id))
    repositorio.registrar(_evento(otro.id))
    sesion.commit()

    assert repositorio.del_turno(uno.id) == [del_uno]


def test_del_turno_sin_eventos_devuelve_lista_vacia(sesion: Session, mundo: dict) -> None:
    turno = _turno(sesion, mundo)

    assert RepositorioHistorialSqlAlchemy(sesion).del_turno(turno.id) == []


@pytest.mark.parametrize(("pedir_el_999", "esperado"), [(False, True), (True, False)])
def test_existe_turno_distingue_un_turno_guardado_de_uno_inexistente(
    sesion: Session, mundo: dict, pedir_el_999: bool, esperado: bool
) -> None:
    turno = _turno(sesion, mundo)

    existe = RepositorioAgendaSqlAlchemy(sesion).existe_turno(999 if pedir_el_999 else turno.id)

    assert existe is esperado


def test_la_unidad_de_trabajo_expone_historial_sobre_la_misma_sesion_que_agenda(
    sesion: Session, fabrica_sesiones, uow, mundo: dict
) -> None:
    nuevo = Turno(
        consultorio_id=mundo["consultorio"].id,
        paciente_id=mundo["paciente"].id,
        profesional_id=mundo["profesional"].id,
        sillon_id=mundo["sillon"].id,
        prestacion_id=mundo["prestacion"].id,
        inicio=a_las(10),
        fin=a_las(10, 30),
        duracion_minutos=30,
        estado=EstadoTurno.RESERVADO,
        creado_en=RELOJ_FIJO,
    )

    with pytest.raises(RuntimeError, match="falla despues de registrar"):
        with uow:
            guardado = uow.agenda.agregar(nuevo)
            uow.historial.registrar(_evento(guardado.id))
            raise RuntimeError("falla despues de registrar")

    # La misma sesión: el rollback deshizo juntos el turno y el evento.
    with fabrica_sesiones() as lectura:
        assert lectura.scalars(select(TurnoModelo)).all() == []
        assert RepositorioHistorialSqlAlchemy(lectura).del_turno(guardado.id) == []


def test_la_unidad_de_trabajo_confirma_el_turno_y_su_evento_juntos(
    sesion: Session, fabrica_sesiones, uow, mundo: dict
) -> None:
    turno = _turno(sesion, mundo)

    with uow:
        registrado = uow.historial.registrar(_evento(turno.id))

    with fabrica_sesiones() as lectura:
        assert RepositorioHistorialSqlAlchemy(lectura).del_turno(turno.id) == [registrado]
