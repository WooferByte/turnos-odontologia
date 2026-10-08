"""Fixtures compartidos: una base SQLite en memoria nueva por test (D12, regla dura 6)."""
from collections.abc import Iterator
from datetime import datetime

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.domain.tiempo import UTC
from app.infrastructure.db.modelos import Base
from app.infrastructure.db.motor import crear_engine_en_memoria

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
