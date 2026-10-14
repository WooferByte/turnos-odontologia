"""Perfil opcional con PostgreSQL: migraciones y esquema (INF-1, INF-4)."""
import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import DateTime, Engine, inspect, select, text
from sqlalchemy.orm import Session

from app.infrastructure.db.modelos import Base, TurnoModelo
from app.infrastructure.db.tipos import FechaHoraUTC
from tests.conftest import a_las
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
)

TABLAS_DE_C01 = {"consultorio", "profesional", "sillon", "prestacion", "paciente", "turno"}
TABLAS_DEL_MODELO = set(Base.metadata.tables)

pytestmark = pytest.mark.postgres


def test_el_perfil_se_conecta_a_postgresql(sesion: Session) -> None:
    assert sesion.execute(text("SELECT 1")).scalar_one() == 1


def test_inf1_base_vacia_migrada_queda_con_el_esquema_del_modelo(engine: Engine) -> None:
    with engine.connect() as conexion:
        inspector = inspect(conexion)
        assert set(inspector.get_table_names()) == TABLAS_DEL_MODELO | {"alembic_version"}

        contexto = MigrationContext.configure(conexion, opts={"compare_type": True})
        assert compare_metadata(contexto, Base.metadata) == []

        for tabla in Base.metadata.sorted_tables:
            columnas = {c["name"]: c["type"] for c in inspector.get_columns(tabla.name)}
            for columna in tabla.columns:
                if isinstance(columna.type, (DateTime, FechaHoraUTC)):
                    assert columnas[columna.name].timezone is True, f"{tabla.name}.{columna.name}"


def test_inf1_deshacer_las_migraciones_deja_la_base_vacia(engine: Engine, config_alembic: Config) -> None:
    command.downgrade(config_alembic, "base")

    with engine.connect() as conexion:
        assert set(inspect(conexion).get_table_names()) == {"alembic_version"}
        restricciones = conexion.execute(
            text(
                "SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace "
                "WHERE n.nspname = 'public' AND c.conrelid::regclass::text <> 'alembic_version'"
            )
        ).scalar_one()
        assert restricciones == 0

    command.upgrade(config_alembic, "head")

    with engine.connect() as conexion:
        assert set(inspect(conexion).get_table_names()) == TABLAS_DEL_MODELO | {"alembic_version"}


def test_inf1_deshacer_las_migraciones_del_historial_deja_el_esquema_de_c01(
    engine: Engine, config_alembic: Config, sesion: Session
) -> None:
    consultorio = un_consultorio(sesion)
    un_turno(
        sesion,
        paciente=un_paciente(sesion, consultorio),
        profesional=un_profesional(sesion, consultorio),
        sillon=un_sillon(sesion, consultorio),
        prestacion=una_prestacion(sesion, consultorio),
        inicio=a_las(10),
    )
    with engine.connect() as conexion:
        assert "evento_turno" in inspect(conexion).get_table_names()

    command.downgrade(config_alembic, "0002")

    with engine.connect() as conexion:
        assert set(inspect(conexion).get_table_names()) == TABLAS_DE_C01 | {"alembic_version"}
    with Session(engine) as lectura:
        assert len(lectura.scalars(select(TurnoModelo)).all()) == 1
