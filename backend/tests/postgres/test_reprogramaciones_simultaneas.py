"""Perfil opcional con PostgreSQL: reprogramaciones simultáneas (REP-1e; RN-AG-10c, DD-04, D337).

Sin mocks: sesiones, repositorio, unidad de trabajo y casos de uso reales, contra PostgreSQL. Corren
solo con el marcador ``postgres`` (SQLite no puede probar la serialización de escrituras, DD-03).
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Barrier

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.crear_turno import CrearTurnoComando, crear_turno
from app.application.reprogramar_turno import ReprogramarTurnoComando, reprogramar_turno
from app.domain.errors import ErrorDeSolapamiento
from app.domain.turnos.eventos import Actor, ActorTipo
from app.domain.turnos.turno import Turno
from app.infrastructure.db.modelos import EventoTurnoModelo, TurnoModelo
from app.infrastructure.unidad_de_trabajo import UnidadDeTrabajoSqlAlchemy
from tests.conftest import a_las, reloj_fijo
from tests.postgres.carrera import Escenario, crear_escenario

pytestmark = pytest.mark.postgres


@pytest.fixture
def escenario(sesion: Session) -> Escenario:
    return crear_escenario(sesion)


def _quien(e: Escenario) -> dict:
    return {"actor": Actor(ActorTipo.USUARIO, str(e.usuario.id)), "creado_por": e.usuario.id}


def _crear(engine: Engine, e: Escenario, hora: int, minuto: int = 0) -> Turno:
    fabrica = sessionmaker(bind=engine, expire_on_commit=False)
    return crear_turno(
        CrearTurnoComando(e.paciente.id, e.prestacion.id, a_las(hora, minuto), e.profesional_a.id, e.sillon_1.id),
        UnidadDeTrabajoSqlAlchemy(fabrica),
        reloj_fijo,
        **_quien(e),
    )


def _pedir_a_la_vez(engine: Engine, pedidos):
    """Larga todos los pedidos a la vez desde una barrera; cada uno devuelve su resultado o su error de solapamiento."""
    fabrica = sessionmaker(bind=engine, expire_on_commit=False)
    largada = Barrier(len(pedidos), timeout=10)

    def correr(pedido):
        largada.wait()
        try:
            return pedido(UnidadDeTrabajoSqlAlchemy(fabrica))
        except ErrorDeSolapamiento as error:
            return error

    with ThreadPoolExecutor(max_workers=len(pedidos)) as hilos:
        futuros = [hilos.submit(correr, p) for p in pedidos]
        return [f.result(timeout=30) for f in futuros]


def _reprogramar(e: Escenario, turno_id: int, hora: int):
    comando = ReprogramarTurnoComando(turno_id, a_las(hora))
    return lambda uow: reprogramar_turno(comando, e.usuario.id, uow, reloj_fijo, actor=_quien(e)["actor"])


def _crear_en(e: Escenario, hora: int):
    comando = CrearTurnoComando(e.paciente.id, e.prestacion.id, a_las(hora), e.profesional_a.id, e.sillon_1.id)
    return lambda uow: crear_turno(comando, uow, reloj_fijo, **_quien(e))


def _activos_a_las_16(sesion: Session) -> list[TurnoModelo]:
    sesion.expire_all()
    todos = sesion.scalars(select(TurnoModelo).where(TurnoModelo.inicio == a_las(16))).all()
    return [t for t in todos if t.estado == "reservado"]


def _reprogramados(sesion: Session, turno_id: int) -> list[EventoTurnoModelo]:
    consulta = (
        select(EventoTurnoModelo)
        .where(EventoTurnoModelo.turno_id == turno_id, EventoTurnoModelo.tipo == "reprogramado")
        .order_by(EventoTurnoModelo.id)
    )
    return list(sesion.scalars(consulta))


def test_rep1e_dos_reprogramaciones_al_mismo_hueco_una_gana(
    engine: Engine, sesion: Session, escenario: Escenario
) -> None:
    primero = _crear(engine, escenario, 13)
    segundo = _crear(engine, escenario, 14)

    resultados = _pedir_a_la_vez(
        engine, [_reprogramar(escenario, primero.id, 16), _reprogramar(escenario, segundo.id, 16)]
    )

    rechazos = [r for r in resultados if isinstance(r, ErrorDeSolapamiento)]
    ganadores = [r for r in resultados if isinstance(r, Turno)]
    assert (len(ganadores), len(rechazos)) == (1, 1)
    assert rechazos[0].codigos == ["RN-AG-05", "RN-AG-08"]
    assert [t.id for t in _activos_a_las_16(sesion)] == [ganadores[0].id]
    perdedor = primero.id if ganadores[0].id == segundo.id else segundo.id
    assert _reprogramados(sesion, perdedor) == []
    assert sesion.get(TurnoModelo, perdedor).inicio == (a_las(13) if perdedor == primero.id else a_las(14))


def test_rep1e_una_reprogramacion_y_un_alta_al_mismo_hueco_una_gana(
    engine: Engine, sesion: Session, escenario: Escenario
) -> None:
    existente = _crear(engine, escenario, 13)

    resultados = _pedir_a_la_vez(engine, [_reprogramar(escenario, existente.id, 16), _crear_en(escenario, 16)])

    rechazos = [r for r in resultados if isinstance(r, ErrorDeSolapamiento)]
    assert len(rechazos) == 1
    assert rechazos[0].codigos == ["RN-AG-05", "RN-AG-08"]
    assert len(_activos_a_las_16(sesion)) == 1
    se_movio = any(isinstance(r, Turno) and r.id == existente.id for r in resultados)
    assert len(_reprogramados(sesion, existente.id)) == (1 if se_movio else 0)
    sesion.expire_all()
    assert sesion.get(TurnoModelo, existente.id).inicio == (a_las(16) if se_movio else a_las(13))


def test_rep1e_dos_reprogramaciones_del_mismo_turno_se_encadenan(
    engine: Engine, sesion: Session, escenario: Escenario
) -> None:
    turno = _crear(engine, escenario, 13)

    resultados = _pedir_a_la_vez(
        engine, [_reprogramar(escenario, turno.id, 16), _reprogramar(escenario, turno.id, 17)]
    )

    assert all(isinstance(r, Turno) for r in resultados)
    eventos = _reprogramados(sesion, turno.id)
    assert len(eventos) == 2
    assert eventos[0].antes["inicio"] == "2026-11-02T13:00:00Z"
    assert eventos[1].antes == eventos[0].despues  # el segundo leyó el horario que dejó el primero
    sesion.expire_all()
    final = datetime.fromisoformat(eventos[1].despues["inicio"].replace("Z", "+00:00"))
    assert sesion.get(TurnoModelo, turno.id).inicio == final  # queda el horario de la que terminó última
