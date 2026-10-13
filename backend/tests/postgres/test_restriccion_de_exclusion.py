"""Perfil opcional con PostgreSQL: la restricción de exclusión (INF-2, INF-3; DD-04, D75).

Los turnos se guardan directamente con las fábricas, sin pasar por el caso de uso: lo que se
prueba es la base, no la validación de dominio.
"""
from datetime import timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.puertos import SolapamientoEnLaBase
from app.domain.turnos.estados import ESTADOS_ACTIVOS, EstadoTurno
from app.domain.turnos.turno import Turno
from app.infrastructure.db.modelos import TurnoModelo
from app.infrastructure.unidad_de_trabajo import UnidadDeTrabajoSqlAlchemy
from tests.conftest import RELOJ_FIJO, a_las
from tests.factories import un_turno
from tests.postgres.carrera import Escenario, crear_escenario

pytestmark = pytest.mark.postgres

SQLSTATE_EXCLUSION = "23P01"
ESTADOS_NO_ACTIVOS = sorted(set(EstadoTurno) - ESTADOS_ACTIVOS)


@pytest.fixture
def escenario(sesion: Session) -> Escenario:
    return crear_escenario(sesion)


def guardar(sesion: Session, e: Escenario, profesional, sillon, inicio, estado="reservado"):
    return un_turno(
        sesion,
        paciente=e.paciente,
        profesional=profesional,
        sillon=sillon,
        prestacion=e.prestacion,
        inicio=inicio,
        estado=estado,
    )


def cantidad_de_turnos(sesion: Session) -> int:
    return sesion.scalar(select(func.count()).select_from(TurnoModelo))


def exigir_exclusion(sesion: Session, e: Escenario, nombre_de_restriccion: str, **turno) -> None:
    """El alta se rechaza con 23P01 y la restricción esperada, y no deja nada guardado."""
    with pytest.raises(IntegrityError) as capturado:
        guardar(sesion, e, **turno)
    sesion.rollback()
    assert capturado.value.orig.sqlstate == SQLSTATE_EXCLUSION
    assert capturado.value.orig.diag.constraint_name == nombre_de_restriccion
    assert cantidad_de_turnos(sesion) == 1


def test_inf2_la_base_rechaza_el_solapamiento_de_e2(sesion: Session, escenario: Escenario) -> None:
    guardar(sesion, escenario, escenario.profesional_a, escenario.sillon_1, a_las(10))

    exigir_exclusion(
        sesion,
        escenario,
        "ex_turno_profesional_sin_solapamiento",
        profesional=escenario.profesional_a,
        sillon=escenario.sillon_2,
        inicio=a_las(10, 15),
    )


def test_inf2_la_base_rechaza_el_solapamiento_de_e3(sesion: Session, escenario: Escenario) -> None:
    guardar(sesion, escenario, escenario.profesional_a, escenario.sillon_1, a_las(10))

    exigir_exclusion(
        sesion,
        escenario,
        "ex_turno_sillon_sin_solapamiento",
        profesional=escenario.profesional_b,
        sillon=escenario.sillon_1,
        inicio=a_las(10),
    )


@pytest.mark.parametrize("estado", sorted(ESTADOS_ACTIVOS))
def test_inf2_cualquier_estado_activo_bloquea(
    sesion: Session, escenario: Escenario, estado: EstadoTurno
) -> None:
    guardar(sesion, escenario, escenario.profesional_a, escenario.sillon_1, a_las(10), estado)

    exigir_exclusion(
        sesion,
        escenario,
        "ex_turno_profesional_sin_solapamiento",
        profesional=escenario.profesional_a,
        sillon=escenario.sillon_2,
        inicio=a_las(10, 29),
    )


def test_inf3_la_base_acepta_el_turno_contiguo_de_e5(sesion: Session, escenario: Escenario) -> None:
    guardar(sesion, escenario, escenario.profesional_a, escenario.sillon_1, a_las(10))

    guardar(sesion, escenario, escenario.profesional_a, escenario.sillon_1, a_las(10, 30))
    guardar(sesion, escenario, escenario.profesional_a, escenario.sillon_1, a_las(9, 30))

    assert cantidad_de_turnos(sesion) == 3


@pytest.mark.parametrize("estado", ESTADOS_NO_ACTIVOS)
def test_inf3_un_turno_no_activo_no_bloquea(
    sesion: Session, escenario: Escenario, estado: EstadoTurno
) -> None:
    guardar(sesion, escenario, escenario.profesional_a, escenario.sillon_1, a_las(10), estado)

    guardar(sesion, escenario, escenario.profesional_a, escenario.sillon_1, a_las(10), "reservado")

    assert cantidad_de_turnos(sesion) == 2


def un_turno_de_dominio(e: Escenario, profesional, sillon, inicio, **cambios) -> Turno:
    datos = {
        "consultorio_id": profesional.consultorio_id,
        "paciente_id": e.paciente.id,
        "profesional_id": profesional.id,
        "sillon_id": sillon.id,
        "prestacion_id": e.prestacion.id,
        "inicio": inicio,
        "fin": inicio + timedelta(minutes=30),
        "duracion_minutos": 30,
        "estado": EstadoTurno.RESERVADO,
        "creado_en": RELOJ_FIJO,
    }
    return Turno(**{**datos, **cambios})


@pytest.mark.parametrize(
    ("profesional", "sillon", "recurso"),
    [("profesional_a", "sillon_2", "profesional"), ("profesional_b", "sillon_1", "sillon")],
)
def test_inf2_el_repositorio_identifica_el_recurso_en_conflicto(
    sesion: Session,
    uow: UnidadDeTrabajoSqlAlchemy,
    escenario: Escenario,
    profesional: str,
    sillon: str,
    recurso: str,
) -> None:
    guardar(sesion, escenario, escenario.profesional_a, escenario.sillon_1, a_las(10))
    nuevo = un_turno_de_dominio(
        escenario, getattr(escenario, profesional), getattr(escenario, sillon), a_las(10, 15)
    )

    with pytest.raises(SolapamientoEnLaBase) as capturado:
        with uow:
            uow.agenda.agregar(nuevo)

    assert capturado.value.recurso == recurso
    assert cantidad_de_turnos(sesion) == 1


def test_otro_error_de_integridad_no_se_traduce(
    sesion: Session, uow: UnidadDeTrabajoSqlAlchemy, escenario: Escenario
) -> None:
    sin_paciente = un_turno_de_dominio(
        escenario, escenario.profesional_a, escenario.sillon_1, a_las(10), paciente_id=999_999
    )

    with pytest.raises(IntegrityError) as capturado:
        with uow:
            uow.agenda.agregar(sin_paciente)

    assert capturado.value.orig.sqlstate == "23503"
    assert cantidad_de_turnos(sesion) == 0
