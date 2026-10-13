"""Perfil opcional con PostgreSQL: el bloqueo de fila del profesional y del sillón (E11; design I8).

Sin mocks: sesiones y repositorio reales. Cada espera se observa en ``pg_stat_activity`` y
tiene tope, para que un fallo no cuelgue la corrida.
"""
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as TiempoAgotado

import pytest
from sqlalchemy import Engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.repositories.agenda import RepositorioAgendaSqlAlchemy
from tests.conftest import a_las
from tests.postgres.carrera import (
    TOPE_DE_ESPERA,
    Escenario,
    bloquear_en_otro_hilo,
    crear_escenario,
    esperar_a_que_haya_una_sesion_bloqueada,
    turno_sin_confirmar,
)

pytestmark = pytest.mark.postgres


@pytest.fixture
def escenario(sesion: Session) -> Escenario:
    return crear_escenario(sesion)


def _la_segunda_espera_a_la_primera(
    engine: Engine, primera: tuple[int, int], segunda: tuple[int, int]
) -> None:
    fabrica = sessionmaker(bind=engine, expire_on_commit=False)
    with fabrica() as sesion_que_retiene, ThreadPoolExecutor(max_workers=1) as hilos:
        RepositorioAgendaSqlAlchemy(sesion_que_retiene).bloquear_recursos(*primera)
        futuro = bloquear_en_otro_hilo(engine, hilos, *segunda)
        try:
            esperar_a_que_haya_una_sesion_bloqueada(engine)
            assert not futuro.done()  # sigue esperando mientras la primera no confirma
        finally:
            sesion_que_retiene.commit()
        futuro.result(timeout=TOPE_DE_ESPERA)  # al confirmar la primera, continúa


def test_dos_bloqueos_del_mismo_profesional_se_serializan(
    engine: Engine, escenario: Escenario
) -> None:
    e = escenario
    _la_segunda_espera_a_la_primera(
        engine, (e.profesional_a.id, e.sillon_1.id), (e.profesional_a.id, e.sillon_2.id)
    )


def test_dos_bloqueos_del_mismo_sillon_se_serializan(
    engine: Engine, escenario: Escenario
) -> None:
    e = escenario
    _la_segunda_espera_a_la_primera(
        engine, (e.profesional_a.id, e.sillon_1.id), (e.profesional_b.id, e.sillon_1.id)
    )


def test_dos_bloqueos_de_recursos_distintos_no_se_esperan(
    engine: Engine, escenario: Escenario
) -> None:
    e = escenario
    fabrica = sessionmaker(bind=engine, expire_on_commit=False)
    with fabrica() as sesion_que_retiene, ThreadPoolExecutor(max_workers=1) as hilos:
        RepositorioAgendaSqlAlchemy(sesion_que_retiene).bloquear_recursos(
            e.profesional_a.id, e.sillon_1.id
        )
        try:
            futuro = bloquear_en_otro_hilo(engine, hilos, e.profesional_b.id, e.sillon_2.id)
            try:
                futuro.result(timeout=TOPE_DE_ESPERA)  # termina sin que la primera confirme
            except TiempoAgotado:
                pytest.fail("un bloqueo de recursos distintos quedó esperando")
        finally:
            sesion_que_retiene.commit()


def test_el_bloqueo_no_frena_una_insercion_que_solo_referencia_al_profesional(
    engine: Engine, escenario: Escenario
) -> None:
    """FOR NO KEY UPDATE no choca con la clave foránea de un turno de otro horario."""
    e = escenario
    fabrica = sessionmaker(bind=engine, expire_on_commit=False)
    with fabrica() as sesion_que_retiene, ThreadPoolExecutor(max_workers=1) as hilos:
        RepositorioAgendaSqlAlchemy(sesion_que_retiene).bloquear_recursos(
            e.profesional_a.id, e.sillon_1.id
        )

        def insertar() -> int:
            with fabrica() as otra:
                id_turno = turno_sin_confirmar(otra, e, e.profesional_a, e.sillon_1, a_las(15))
                otra.commit()
                return id_turno

        try:
            hilos.submit(insertar).result(timeout=TOPE_DE_ESPERA)
        except TiempoAgotado:
            pytest.fail("el bloqueo frenó una inserción que solo referencia al profesional")
        finally:
            sesion_que_retiene.commit()


def test_en_postgresql_el_bloqueo_es_for_no_key_update_primero_el_profesional(
    engine: Engine, sesion: Session, escenario: Escenario
) -> None:
    sentencias: list[str] = []

    def registrar(conexion, cursor, sentencia, parametros, contexto, varias):
        sentencias.append(" ".join(sentencia.split()))

    event.listen(engine, "before_cursor_execute", registrar)
    try:
        RepositorioAgendaSqlAlchemy(sesion).bloquear_recursos(
            escenario.profesional_a.id, escenario.sillon_1.id
        )
    finally:
        event.remove(engine, "before_cursor_execute", registrar)
        sesion.rollback()

    assert len(sentencias) == 2
    assert "FROM profesional" in sentencias[0] and sentencias[0].endswith("FOR NO KEY UPDATE")
    assert "FROM sillon" in sentencias[1] and sentencias[1].endswith("FOR NO KEY UPDATE")
