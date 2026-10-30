"""Perfil opcional con PostgreSQL: marcados de asistencia simultáneos (ASI-1e; RN-AG-12, DD-04, D362).

Sin mocks: sesiones, repositorio, unidad de trabajo y casos de uso reales, contra PostgreSQL. Corren
solo con el marcador ``postgres`` (SQLite no puede probar la serialización de escrituras, DD-03). La
carrera se fuerza como en ``test_cancelaciones_simultaneas.py``: otra sesión retiene la fila del turno,
se espera con ``pg_stat_activity`` a que los dos pedidos estén bloqueados y recién entonces se suelta.
"""
from datetime import UTC, datetime

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.application.cancelar_turno import CancelarTurnoComando, cancelar_turno
from app.application.marcar_asistencia import MarcarAsistenciaComando, marcar_asistencia
from app.domain.errors import TransicionInvalida
from app.domain.turnos.estados import EstadoTurno
from app.domain.turnos.eventos import Actor, ActorTipo
from app.domain.turnos.turno import Turno
from app.infrastructure.db.modelos import EventoTurnoModelo, PacienteModelo, TurnoModelo
from tests.conftest import reloj_fijo
from tests.postgres.carrera import Escenario, crear_escenario
from tests.postgres.test_cancelaciones_simultaneas import _crear, _pedir_con_el_turno_retenido

pytestmark = pytest.mark.postgres

AHORA = datetime(2026, 11, 2, 13, 10, tzinfo=UTC)  # después del turno de las 13:00


@pytest.fixture
def escenario(sesion: Session) -> Escenario:
    return crear_escenario(sesion)


def _actor(e: Escenario) -> Actor:
    return Actor(ActorTipo.USUARIO, str(e.usuario.id))


def _marcar(e: Escenario, turno_id: int, estado: EstadoTurno):
    comando = MarcarAsistenciaComando(turno_id, estado)
    return lambda uow: marcar_asistencia(comando, e.usuario.id, uow, lambda: AHORA, actor=_actor(e))


def _cancelar(e: Escenario, turno_id: int, estado: EstadoTurno):
    comando = CancelarTurnoComando(turno_id, estado)
    return lambda uow: cancelar_turno(comando, e.usuario.id, uow, reloj_fijo, actor=_actor(e))


def _tipos(sesion: Session, turno_id: int) -> list[str]:
    sesion.expire_all()
    consulta = select(EventoTurnoModelo.tipo).where(EventoTurnoModelo.turno_id == turno_id).order_by(EventoTurnoModelo.id)
    return list(sesion.scalars(consulta))


def test_asi1e_dos_marcados_del_mismo_turno_uno_gana(
    engine: Engine, sesion: Session, escenario: Escenario
) -> None:
    turno = _crear(engine, escenario, 13)

    resultados = _pedir_con_el_turno_retenido(
        engine,
        turno.id,
        [
            _marcar(escenario, turno.id, EstadoTurno.ATENDIDO),
            _marcar(escenario, turno.id, EstadoTurno.AUSENTE),
        ],
    )

    ganadores = [r for r in resultados if isinstance(r, Turno)]
    rechazos = [r for r in resultados if isinstance(r, TransicionInvalida)]
    assert (len(ganadores), len(rechazos)) == (1, 1)
    assert rechazos[0].codigos == ["RN-AG-12"]
    assert _tipos(sesion, turno.id) == ["creado", "estado_cambiado"]
    assert sesion.get(TurnoModelo, turno.id).estado == ganadores[0].estado.value
    # es_nuevo sigue a quien ganó: solo un atendido la deja en falso (D52)
    assert sesion.get(PacienteModelo, escenario.paciente.id).es_nuevo is (ganadores[0].estado is EstadoTurno.AUSENTE)


def test_asi1e_marcado_y_cancelacion_se_serializan(
    engine: Engine, sesion: Session, escenario: Escenario
) -> None:
    turno = _crear(engine, escenario, 13)

    resultados = _pedir_con_el_turno_retenido(
        engine,
        turno.id,
        [
            _marcar(escenario, turno.id, EstadoTurno.ATENDIDO),
            _cancelar(escenario, turno.id, EstadoTurno.CANCELADO_PACIENTE),
        ],
    )

    ganadores = [r for r in resultados if isinstance(r, Turno)]
    rechazos = [r for r in resultados if isinstance(r, TransicionInvalida)]
    assert (len(ganadores), len(rechazos)) == (1, 1)
    assert rechazos[0].codigos == ["RN-AG-12"]
    tipos = _tipos(sesion, turno.id)
    assert tipos in (["creado", "estado_cambiado"], ["creado", "cancelado"])
    assert len(tipos) == 2  # un solo evento además del creado
    assert sesion.get(TurnoModelo, turno.id).estado == ganadores[0].estado.value
