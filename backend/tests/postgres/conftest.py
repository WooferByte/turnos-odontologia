"""Fixtures del perfil opcional con PostgreSQL (D75, design I9).

Redefine ``engine``; ``fabrica_sesiones``, ``sesion`` y ``uow`` de
``tests/conftest.py`` se reutilizan porque cuelgan de él.
"""
import os
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

VARIABLE = "TEST_DATABASE_URL"
COMO_LEVANTARLO = (
    "levantá la base con 'docker compose up -d postgres' y definí "
    f"{VARIABLE}=postgresql+psycopg://app:app@localhost:5432/turnos_test"
)


@pytest.fixture
def engine() -> Iterator[Engine]:
    url = os.environ.get(VARIABLE)
    if not url:
        pytest.skip(f"PostgreSQL no disponible: falta {VARIABLE}; {COMO_LEVANTARLO}")
    base = make_url(url).database or ""
    if not base.endswith("_test"):
        # No es "PostgreSQL no disponible": borraría una base que no es de tests.
        pytest.fail(f"{VARIABLE} apunta a la base '{base}', que no termina en _test")
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.begin() as conexion:
            conexion.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            conexion.execute(text("CREATE SCHEMA public"))
    except OperationalError as error:
        engine.dispose()
        pytest.skip(f"PostgreSQL no disponible ({type(error.orig).__name__}); {COMO_LEVANTARLO}")
    yield engine
    engine.dispose()
