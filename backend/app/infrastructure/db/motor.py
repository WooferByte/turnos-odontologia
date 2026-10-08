"""Engine de SQLite en memoria, el mismo para la demo y para los tests (D12)."""
from sqlalchemy import Engine, create_engine
from sqlalchemy.pool import StaticPool


def crear_engine_en_memoria() -> Engine:
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
