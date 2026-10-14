"""Perfil opcional con PostgreSQL: reservas simultáneas del mismo hueco (E11; RN-AG-10c, D85).

Sin mocks: sesiones, repositorio, unidad de trabajo y caso de uso reales, contra PostgreSQL.
"""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_reloj
from app.application.crear_turno import CrearTurnoComando, crear_turno
from app.domain.errors import ErrorDeSolapamiento
from app.infrastructure.db.modelos import EventoTurnoModelo, TurnoModelo
from app.infrastructure.repositories.agenda import RepositorioAgendaSqlAlchemy
from app.infrastructure.unidad_de_trabajo import UnidadDeTrabajoSqlAlchemy
from app.main import crear_app
from tests.conftest import a_las, reloj_fijo
from tests.postgres.carrera import Escenario, ReservaGanadora, carrera, crear_escenario

pytestmark = pytest.mark.postgres


@pytest.fixture
def escenario(sesion: Session) -> Escenario:
    return crear_escenario(sesion)


@pytest.fixture
def uow(engine: Engine) -> UnidadDeTrabajoSqlAlchemy:
    return UnidadDeTrabajoSqlAlchemy(sessionmaker(bind=engine, expire_on_commit=False))


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
    engine: Engine, sesion: Session, escenario: Escenario, uow: UnidadDeTrabajoSqlAlchemy
) -> None:
    pedido = comando(escenario, escenario.profesional_a, escenario.sillon_1, a_las(10))
    ganador = ReservaGanadora(escenario, escenario.profesional_a, escenario.sillon_1, a_las(10))

    with pytest.raises(ErrorDeSolapamiento) as capturado:
        carrera(engine, ganador, lambda: crear_turno(pedido, uow))

    assert capturado.value.codigos == ["RN-AG-05", "RN-AG-08"]
    assert [c.turno_id for c in capturado.value.conflictos] == [ganador.id, ganador.id]
    assert cantidad_de_turnos(sesion) == 1


def test_e11_la_carrera_por_un_solo_recurso_informa_solo_ese_codigo(
    engine: Engine, sesion: Session, escenario: Escenario, uow: UnidadDeTrabajoSqlAlchemy
) -> None:
    pedido = comando(escenario, escenario.profesional_a, escenario.sillon_2, a_las(10, 15))
    ganador = ReservaGanadora(escenario, escenario.profesional_a, escenario.sillon_1, a_las(10))

    with pytest.raises(ErrorDeSolapamiento) as capturado:
        carrera(engine, ganador, lambda: crear_turno(pedido, uow))

    assert capturado.value.codigos == ["RN-AG-05"]
    assert [c.turno_id for c in capturado.value.conflictos] == [ganador.id]
    assert cantidad_de_turnos(sesion) == 1


def test_e11_de_ocho_peticiones_a_la_vez_se_crea_un_solo_turno(
    engine: Engine, sesion: Session, escenario: Escenario
) -> None:
    peticiones = 8
    fabrica = sessionmaker(bind=engine, expire_on_commit=False)
    pedido = comando(escenario, escenario.profesional_a, escenario.sillon_1, a_las(10))
    largada = Barrier(peticiones, timeout=10)

    def pedir():
        largada.wait()
        try:
            return crear_turno(pedido, UnidadDeTrabajoSqlAlchemy(fabrica))
        except ErrorDeSolapamiento as error:
            return error

    with ThreadPoolExecutor(max_workers=peticiones) as hilos:
        futuros = [hilos.submit(pedir) for _ in range(peticiones)]
        resultados = [f.result(timeout=30) for f in futuros]

    rechazos = [r for r in resultados if isinstance(r, ErrorDeSolapamiento)]
    creados = [r for r in resultados if not isinstance(r, ErrorDeSolapamiento)]
    assert len(creados) == 1
    assert creados[0].estado == "reservado"
    assert len(rechazos) == peticiones - 1
    assert all(r.codigos == ["RN-AG-05", "RN-AG-08"] for r in rechazos)
    assert cantidad_de_turnos(sesion) == 1


def test_e9_de_ocho_reservas_simultaneas_queda_un_solo_evento(
    engine: Engine, sesion: Session, escenario: Escenario
) -> None:
    peticiones = 8
    fabrica = sessionmaker(bind=engine, expire_on_commit=False)
    pedido = comando(escenario, escenario.profesional_a, escenario.sillon_1, a_las(10))
    largada = Barrier(peticiones, timeout=10)

    def pedir():
        largada.wait()
        try:
            return crear_turno(pedido, UnidadDeTrabajoSqlAlchemy(fabrica), reloj_fijo)
        except ErrorDeSolapamiento as error:
            return error

    with ThreadPoolExecutor(max_workers=peticiones) as hilos:
        futuros = [hilos.submit(pedir) for _ in range(peticiones)]
        resultados = [f.result(timeout=30) for f in futuros]

    creados = [r for r in resultados if not isinstance(r, ErrorDeSolapamiento)]
    assert len(creados) == 1
    eventos = sesion.scalars(select(EventoTurnoModelo)).all()
    assert [(e.turno_id, e.tipo) for e in eventos] == [(creados[0].id, "creado")]
    assert cantidad_de_turnos(sesion) == 1


def test_e11_post_turnos_responde_409_al_que_pierde_la_carrera(
    engine: Engine, sesion: Session, escenario: Escenario
) -> None:
    app = crear_app(engine)
    app.dependency_overrides[get_reloj] = lambda: reloj_fijo
    cliente = TestClient(app)
    peticion = {
        "paciente_id": escenario.paciente.id,
        "prestacion_id": escenario.prestacion.id,
        "inicio": "2026-11-02T10:00:00Z",
        "profesional_id": escenario.profesional_a.id,
        "sillon_id": escenario.sillon_1.id,
    }
    ganador = ReservaGanadora(escenario, escenario.profesional_a, escenario.sillon_1, a_las(10))

    _, respuesta = carrera(engine, ganador, lambda: cliente.post("/turnos", json=peticion))

    assert respuesta.status_code == 409
    assert respuesta.headers["content-type"] == "application/problem+json"
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-AG-05", "RN-AG-08"]
    assert cuerpo["conflictos"] == [
        {
            "codigo": "RN-AG-05",
            "recurso": "profesional",
            "recurso_id": escenario.profesional_a.id,
            "turno_id": ganador.id,
        },
        {
            "codigo": "RN-AG-08",
            "recurso": "sillon",
            "recurso_id": escenario.sillon_1.id,
            "turno_id": ganador.id,
        },
    ]
    assert cantidad_de_turnos(sesion) == 1


class _AgendaQueCuenta:
    """Envuelve el repositorio real y cuenta las llamadas, sin cambiar lo que devuelve."""

    def __init__(self, agenda, llamadas: list[str]) -> None:
        self._agenda = agenda
        self._llamadas = llamadas

    def __getattr__(self, nombre: str):
        atributo = getattr(self._agenda, nombre)
        if not callable(atributo):
            return atributo

        def registrar(*args, **kwargs):
            self._llamadas.append(nombre)
            return atributo(*args, **kwargs)

        return registrar


class _UnidadQueCuenta(UnidadDeTrabajoSqlAlchemy):
    def __init__(self, fabrica, llamadas: list[str]) -> None:
        super().__init__(fabrica)
        self._llamadas = llamadas

    def __enter__(self):
        super().__enter__()
        self.agenda = _AgendaQueCuenta(self.agenda, self._llamadas)
        return self


def test_e11_la_segunda_reserva_espera_el_bloqueo_y_se_rechaza_sin_reintento(
    engine: Engine, sesion: Session, escenario: Escenario
) -> None:
    fabrica = sessionmaker(bind=engine, expire_on_commit=False)
    llamadas: list[str] = []
    pedido = comando(escenario, escenario.profesional_a, escenario.sillon_1, a_las(10))
    ganador = ReservaGanadora(escenario, escenario.profesional_a, escenario.sillon_1, a_las(10))

    def ganador_con_bloqueo(sesion_ganadora: Session) -> int:
        RepositorioAgendaSqlAlchemy(sesion_ganadora).bloquear_recursos(
            escenario.profesional_a.id, escenario.sillon_1.id
        )
        return ganador(sesion_ganadora)

    with pytest.raises(ErrorDeSolapamiento) as capturado:
        carrera(
            engine,
            ganador_con_bloqueo,
            lambda: crear_turno(pedido, _UnidadQueCuenta(fabrica, llamadas)),
        )

    assert capturado.value.codigos == ["RN-AG-05", "RN-AG-08"]
    assert [c.turno_id for c in capturado.value.conflictos] == [ganador.id, ganador.id]
    # Un solo intento: leyó los ocupados una vez, con el turno ya confirmado, y nunca insertó,
    # así que la base no llegó a levantar ni 23P01 ni 40P01.
    assert llamadas.count("ocupados_en_el_intervalo") == 1
    assert "agregar" not in llamadas
    assert cantidad_de_turnos(sesion) == 1
