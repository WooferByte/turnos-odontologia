"""Entorno de Alembic: solo modo en línea, solo PostgreSQL (design I6).

La URL sale de la opción ``sqlalchemy.url`` si un programa la definió (los tests
del perfil ``postgres``) y si no de ``DATABASE_URL``. Nunca de ``alembic.ini``.
"""
from logging.config import fileConfig

from alembic import context

from app.infrastructure.configuracion import leer_database_url
from app.infrastructure.db.modelos import Base
from app.infrastructure.db.motor import crear_engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def run_migrations_online() -> None:
    url = config.get_main_option("sqlalchemy.url") or leer_database_url()
    engine = crear_engine(url)
    try:
        with engine.connect() as conexion:
            context.configure(
                connection=conexion,
                target_metadata=target_metadata,
                compare_type=True,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    raise RuntimeError("Las migraciones solo se aplican en línea contra PostgreSQL (design I6).")

run_migrations_online()
