"""Perfil opcional con PostgreSQL: la restricción de exclusión (INF-2, INF-3; DD-04, D75).

Los turnos se guardan directamente con las fábricas, sin pasar por el caso de uso: lo que se
prueba es la base, no la validación de dominio.
"""
from dataclasses import dataclass

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.turnos.estados import ESTADOS_ACTIVOS, EstadoTurno
from app.infrastructure.db.modelos import (
    PacienteModelo,
    PrestacionModelo,
    ProfesionalModelo,
    SillonModelo,
    TurnoModelo,
)
from tests.conftest import a_las
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
)

pytestmark = pytest.mark.postgres

SQLSTATE_EXCLUSION = "23P01"
ESTADOS_NO_ACTIVOS = sorted(set(EstadoTurno) - ESTADOS_ACTIVOS)


@dataclass
class Escenario:
    paciente: PacienteModelo
    prestacion: PrestacionModelo
    profesional_a: ProfesionalModelo
    profesional_b: ProfesionalModelo
    sillon_1: SillonModelo
    sillon_2: SillonModelo


@pytest.fixture
def escenario(sesion: Session) -> Escenario:
    consultorio = un_consultorio(sesion)
    return Escenario(
        paciente=un_paciente(sesion, consultorio),
        prestacion=una_prestacion(sesion, consultorio),
        profesional_a=un_profesional(sesion, consultorio, nombre="Profesional A"),
        profesional_b=un_profesional(sesion, consultorio, nombre="Profesional B"),
        sillon_1=un_sillon(sesion, consultorio, nombre="Sillón 1"),
        sillon_2=un_sillon(sesion, consultorio, nombre="Sillón 2"),
    )


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
