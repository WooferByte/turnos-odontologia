"""Fixtures compartidos: una base SQLite en memoria nueva por test (D12, regla dura 6)."""
from collections.abc import Iterator
from datetime import datetime

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.domain.tiempo import UTC
from app.infrastructure.db.modelos import Base
from app.infrastructure.db.motor import crear_engine_en_memoria
from app.infrastructure.unidad_de_trabajo import UnidadDeTrabajoSqlAlchemy

RELOJ_FIJO = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)


def reloj_fijo() -> datetime:
    return RELOJ_FIJO


@pytest.fixture
def engine() -> Iterator[Engine]:
    engine = crear_engine_en_memoria()
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def fabrica_sesiones(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def sesion(fabrica_sesiones: sessionmaker[Session]) -> Iterator[Session]:
    with fabrica_sesiones() as sesion:
        yield sesion


@pytest.fixture
def uow(fabrica_sesiones: sessionmaker[Session]) -> UnidadDeTrabajoSqlAlchemy:
    return UnidadDeTrabajoSqlAlchemy(fabrica_sesiones)


DIA_DE_PRUEBA = (2026, 11, 2)  # horario compartido por los tests de agenda


def a_las(hora: int, minuto: int = 0) -> datetime:
    """Instante UTC de ``DIA_DE_PRUEBA`` a esa hora y minuto."""
    return datetime(*DIA_DE_PRUEBA, hora, minuto, tzinfo=UTC)
