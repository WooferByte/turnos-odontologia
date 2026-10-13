"""Engines de SQLAlchemy: SQLite en memoria para la demo y los tests (D12) y el de ``DATABASE_URL``."""
from sqlalchemy import Engine, create_engine
from sqlalchemy.pool import StaticPool


def crear_engine_en_memoria() -> Engine:
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def crear_engine(url: str) -> Engine:
    """Engine sincrónico para la base de la URL dada (design I12).

    ``pool_pre_ping`` evita que una conexión caída tras reiniciar PostgreSQL
    rompa la primera petición.
    """
    return create_engine(url, pool_pre_ping=True)
