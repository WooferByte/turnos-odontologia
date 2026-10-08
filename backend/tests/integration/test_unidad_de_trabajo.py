"""La unidad de trabajo confirma al salir sin error y deshace si hubo uno (D12)."""
from datetime import datetime

import pytest
from sqlalchemy import select

from app.domain.tiempo import UTC
from app.domain.turnos.estados import EstadoTurno
from app.domain.turnos.turno import Turno
from app.infrastructure.db.modelos import TurnoModelo
from tests.conftest import RELOJ_FIJO
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
)


def _turno_nuevo(sesion) -> Turno:
    consultorio = un_consultorio(sesion)
    return Turno(
        consultorio_id=consultorio.id,
        paciente_id=un_paciente(sesion, consultorio).id,
        profesional_id=un_profesional(sesion, consultorio).id,
        sillon_id=un_sillon(sesion, consultorio).id,
        prestacion_id=una_prestacion(sesion, consultorio).id,
        inicio=datetime(2026, 11, 2, 10, 0, tzinfo=UTC),
        fin=datetime(2026, 11, 2, 10, 30, tzinfo=UTC),
        duracion_minutos=30,
        estado=EstadoTurno.RESERVADO,
        creado_en=RELOJ_FIJO,
    )


def _cantidad_de_turnos(fabrica_sesiones) -> int:
    with fabrica_sesiones() as sesion:
        return len(sesion.scalars(select(TurnoModelo)).all())


def test_sale_sin_error_confirma_el_turno(sesion, fabrica_sesiones, uow):
    turno = _turno_nuevo(sesion)

    with uow:
        guardado = uow.agenda.agregar(turno)

    assert guardado.id is not None
    assert _cantidad_de_turnos(fabrica_sesiones) == 1


def test_sale_con_error_deshace_lo_ya_enviado_a_la_base(sesion, fabrica_sesiones, uow):
    turno = _turno_nuevo(sesion)

    with pytest.raises(RuntimeError, match="falla despues de agregar"):
        with uow:
            guardado = uow.agenda.agregar(turno)  # ya hizo flush: tiene id
            assert guardado.id is not None
            raise RuntimeError("falla despues de agregar")

    assert _cantidad_de_turnos(fabrica_sesiones) == 0
