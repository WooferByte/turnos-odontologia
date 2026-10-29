"""Perfil opcional con PostgreSQL: cancelaciones simultáneas (CAN-1d; RN-AG-12, RN-AG-18, DD-04, D348).

Sin mocks: sesiones, repositorio, unidad de trabajo y casos de uso reales, contra PostgreSQL. Corren
solo con el marcador ``postgres`` (SQLite no puede probar la serialización de escrituras, DD-03).
"""
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.cancelar_turno import CancelarTurnoComando, cancelar_turno
from app.application.crear_turno import CrearTurnoComando, crear_turno
from app.application.reprogramar_turno import ReprogramarTurnoComando, reprogramar_turno
from app.domain.errors import ErrorDeDominio, TransicionInvalida, TurnoNoReprogramable
from app.domain.turnos.estados import EstadoTurno
from app.domain.turnos.eventos import Actor, ActorTipo
from app.domain.turnos.turno import Turno
from app.infrastructure.db.modelos import EventoTurnoModelo, TurnoModelo
from app.infrastructure.unidad_de_trabajo import UnidadDeTrabajoSqlAlchemy
from tests.conftest import a_las, reloj_fijo
from tests.postgres.carrera import BLOQUEADAS, TOPE_DE_ESPERA, Escenario, crear_escenario

pytestmark = pytest.mark.postgres


@pytest.fixture
def escenario(sesion: Session) -> Escenario:
    return crear_escenario(sesion)


def _actor(e: Escenario) -> Actor:
    return Actor(ActorTipo.USUARIO, str(e.usuario.id))


def _crear(engine: Engine, e: Escenario, hora: int) -> Turno:
    fabrica = sessionmaker(bind=engine, expire_on_commit=False)
    return crear_turno(
        CrearTurnoComando(e.paciente.id, e.prestacion.id, a_las(hora), e.profesional_a.id, e.sillon_1.id),
        UnidadDeTrabajoSqlAlchemy(fabrica),
        reloj_fijo,
        actor=_actor(e),
        creado_por=e.usuario.id,
    )


def _pedir_con_el_turno_retenido(engine: Engine, turno_id: int, pedidos):
    """Fuerza la carrera: otra sesión retiene la fila del turno, los pedidos se largan y quedan esperando.

    Lanzar hilos con una barrera no prueba nada si uno termina antes de que el otro lea (design X6). Acá se
    espera, mirando ``pg_stat_activity``, a que los dos pedidos estén bloqueados y recién entonces la sesión
    que retenía confirma. Sin el bloqueo de fila del turno, los dos habrían leído el estado de antes.
    """
    fabrica = sessionmaker(bind=engine, expire_on_commit=False)

    def correr(pedido):
        try:
            return pedido(UnidadDeTrabajoSqlAlchemy(fabrica))
        except ErrorDeDominio as error:
            return error

    with fabrica() as retenedora, ThreadPoolExecutor(max_workers=len(pedidos)) as hilos:
        retenedora.execute(
            select(TurnoModelo.id).where(TurnoModelo.id == turno_id).with_for_update(key_share=True)
        ).all()
        futuros = [hilos.submit(correr, p) for p in pedidos]
        try:
            _esperar_bloqueadas(engine, len(pedidos))
        finally:
            retenedora.commit()  # suelta a los pedidos aunque la espera haya fallado
        return [f.result(timeout=30) for f in futuros]


def _esperar_bloqueadas(engine: Engine, cantidad: int) -> None:
    limite = time.monotonic() + TOPE_DE_ESPERA
    with engine.connect() as conexion:
        while conexion.execute(BLOQUEADAS).scalar_one() < cantidad:
            conexion.rollback()  # que la próxima consulta vea el estado nuevo
            if time.monotonic() > limite:
                raise AssertionError("los pedidos no quedaron esperando la fila del turno")
            time.sleep(0.02)


def _cancelar(e: Escenario, turno_id: int, estado: EstadoTurno):
    comando = CancelarTurnoComando(turno_id, estado)
    return lambda uow: cancelar_turno(comando, e.usuario.id, uow, reloj_fijo, actor=_actor(e))


def _reprogramar(e: Escenario, turno_id: int, hora: int):
    comando = ReprogramarTurnoComando(turno_id, a_las(hora))
    return lambda uow: reprogramar_turno(comando, e.usuario.id, uow, reloj_fijo, actor=_actor(e))


def _tipos(sesion: Session, turno_id: int) -> list[str]:
    sesion.expire_all()
    consulta = select(EventoTurnoModelo.tipo).where(EventoTurnoModelo.turno_id == turno_id).order_by(EventoTurnoModelo.id)
    return list(sesion.scalars(consulta))


def test_can1d_dos_cancelaciones_del_mismo_turno_una_gana(
    engine: Engine, sesion: Session, escenario: Escenario
) -> None:
    turno = _crear(engine, escenario, 13)

    resultados = _pedir_con_el_turno_retenido(
        engine,
        turno.id,
        [
            _cancelar(escenario, turno.id, EstadoTurno.CANCELADO_PACIENTE),
            _cancelar(escenario, turno.id, EstadoTurno.CANCELADO_PROFESIONAL),
        ],
    )

    ganadores = [r for r in resultados if isinstance(r, Turno)]
    rechazos = [r for r in resultados if isinstance(r, TransicionInvalida)]
    assert (len(ganadores), len(rechazos)) == (1, 1)
    assert rechazos[0].codigos == ["RN-AG-12"]
    assert _tipos(sesion, turno.id) == ["creado", "cancelado"]
    assert sesion.get(TurnoModelo, turno.id).estado == ganadores[0].estado.value


def test_can1d_cancelacion_y_reprogramacion_se_serializan(
    engine: Engine, sesion: Session, escenario: Escenario
) -> None:
    turno = _crear(engine, escenario, 13)

    resultados = _pedir_con_el_turno_retenido(
        engine,
        turno.id,
        [_cancelar(escenario, turno.id, EstadoTurno.CANCELADO_PACIENTE), _reprogramar(escenario, turno.id, 16)],
    )

    tipos = _tipos(sesion, turno.id)
    sesion.expire_all()
    guardado = sesion.get(TurnoModelo, turno.id)
    assert guardado.estado == "cancelado_paciente"  # la cancelación siempre se aplica o el turno ya no existe
    cancelacion = next(r for r in resultados if isinstance(r, Turno) and r.estado.value == "cancelado_paciente")
    assert cancelacion is not None
    if tipos == ["creado", "reprogramado", "cancelado"]:  # la reprogramación llegó primero
        assert all(isinstance(r, Turno) for r in resultados)
        assert guardado.inicio == a_las(16)
    else:  # la cancelación llegó primero: la reprogramación ve un turno terminal
        assert tipos == ["creado", "cancelado"]
        assert any(isinstance(r, TurnoNoReprogramable) and r.codigos == ["RN-AG-18"] for r in resultados)
        assert guardado.inicio == a_las(13)
    assert "reprogramado" not in tipos[tipos.index("cancelado") :]  # nunca un reprogramado después del cancelado
