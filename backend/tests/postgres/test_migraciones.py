"""Perfil opcional con PostgreSQL: migraciones y esquema (INF-1, INF-4)."""
import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Engine, inspect, text
from sqlalchemy.orm import Session

from app.infrastructure.db.modelos import Base

TABLAS_DE_C01 = {"consultorio", "profesional", "sillon", "prestacion", "paciente", "turno"}

pytestmark = pytest.mark.postgres


def test_el_perfil_se_conecta_a_postgresql(sesion: Session) -> None:
    assert sesion.execute(text("SELECT 1")).scalar_one() == 1


def test_inf1_base_vacia_migrada_queda_con_el_esquema_de_c01(engine: Engine) -> None:
    with engine.connect() as conexion:
        inspector = inspect(conexion)
        assert set(inspector.get_table_names()) == TABLAS_DE_C01 | {"alembic_version"}

        contexto = MigrationContext.configure(conexion, opts={"compare_type": True})
        assert compare_metadata(contexto, Base.metadata) == []

        columnas = {c["name"]: c["type"] for c in inspector.get_columns("turno")}
        for nombre in ("inicio", "fin", "creado_en"):
            assert columnas[nombre].timezone is True, nombre
