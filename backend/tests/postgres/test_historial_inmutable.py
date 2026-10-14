"""Perfil opcional con PostgreSQL: el historial es de solo inserción en la base (US-015 CA-1; H11).

El evento se guarda con las fábricas y los intentos de modificarlo son SQL directo: lo que se
prueba es el disparador de la migración ``0004``, no la aplicación (que ni siquiera tiene con qué).
"""
import pytest
from sqlalchemy import Engine, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.infrastructure.db.modelos import EventoTurnoModelo
from tests.conftest import a_las
from tests.factories import (
    un_consultorio,
    un_evento,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
)

pytestmark = pytest.mark.postgres


@pytest.fixture
def turno(sesion: Session):
    consultorio = un_consultorio(sesion)
    return un_turno(
        sesion,
        paciente=un_paciente(sesion, consultorio),
        profesional=un_profesional(sesion, consultorio),
        sillon=un_sillon(sesion, consultorio),
        prestacion=una_prestacion(sesion, consultorio),
        inicio=a_las(10),
    )


def _eventos(engine: Engine) -> list[tuple]:
    """Lo que hay en la tabla, leído con una conexión nueva."""
    with engine.connect() as conexion:
        filas = conexion.execute(
            select(EventoTurnoModelo.id, EventoTurnoModelo.tipo, EventoTurnoModelo.motivo).order_by(
                EventoTurnoModelo.id
            )
        )
        return [tuple(fila) for fila in filas]


@pytest.mark.parametrize(
    "sentencia",
    [
        pytest.param("UPDATE evento_turno SET tipo = 'cancelado'", id="update_del_tipo"),
        pytest.param("DELETE FROM evento_turno", id="delete"),
        pytest.param("TRUNCATE evento_turno", id="truncate"),
    ],
)
def test_ca1_la_base_rechaza_modificar_o_borrar_un_evento(
    engine: Engine, sesion: Session, turno, sentencia: str
) -> None:
    evento = un_evento(sesion, turno, motivo="original")

    with pytest.raises(DBAPIError, match="solo inserción"):
        with engine.begin() as conexion:
            conexion.execute(text(sentencia))

    assert _eventos(engine) == [(evento.id, "creado", "original")]


def test_ca1_la_base_acepta_un_evento_nuevo_del_mismo_turno(
    engine: Engine, sesion: Session, turno
) -> None:
    un_evento(sesion, turno, motivo="primero")

    un_evento(sesion, turno, motivo="segundo")

    assert [motivo for _, _, motivo in _eventos(engine)] == ["primero", "segundo"]
