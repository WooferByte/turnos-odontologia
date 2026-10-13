"""Perfil opcional con PostgreSQL: reservas simultáneas del mismo hueco (E11; RN-AG-10c, D85).

Sin mocks: sesiones, repositorio, unidad de trabajo y caso de uso reales, contra PostgreSQL.
"""
import pytest
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.crear_turno import CrearTurnoComando, crear_turno
from app.domain.errors import ErrorDeSolapamiento
from app.infrastructure.db.modelos import TurnoModelo
from app.infrastructure.unidad_de_trabajo import UnidadDeTrabajoSqlAlchemy
from tests.conftest import a_las
from tests.postgres.carrera import Escenario, carrera, crear_escenario, turno_sin_confirmar

pytestmark = pytest.mark.postgres


@pytest.fixture
def escenario(sesion: Session) -> Escenario:
    return crear_escenario(sesion)


def comando(e: Escenario, profesional, sillon, inicio) -> CrearTurnoComando:
    return CrearTurnoComando(
        paciente_id=e.paciente.id,
        prestacion_id=e.prestacion.id,
        inicio=inicio,
        profesional_id=profesional.id,
        sillon_id=sillon.id,
    )


def cantidad_de_turnos(sesion: Session) -> int:
    return sesion.scalar(select(func.count()).select_from(TurnoModelo))


def test_e11_la_reserva_que_pierde_la_carrera_recibe_el_rechazo_por_solapamiento(
    engine: Engine, sesion: Session, escenario: Escenario
) -> None:
    uow = UnidadDeTrabajoSqlAlchemy(sessionmaker(bind=engine, expire_on_commit=False))
    pedido = comando(escenario, escenario.profesional_a, escenario.sillon_1, a_las(10))
    id_ganador = None

    def ganador(sesion_ganadora: Session) -> int:
        nonlocal id_ganador
        id_ganador = turno_sin_confirmar(
            sesion_ganadora, escenario, escenario.profesional_a, escenario.sillon_1, a_las(10)
        )
        return id_ganador

    with pytest.raises(ErrorDeSolapamiento) as capturado:
        carrera(engine, ganador, lambda: crear_turno(pedido, uow))

    assert capturado.value.codigos == ["RN-AG-05", "RN-AG-08"]
    assert [c.turno_id for c in capturado.value.conflictos] == [id_ganador, id_ganador]
    assert cantidad_de_turnos(sesion) == 1
