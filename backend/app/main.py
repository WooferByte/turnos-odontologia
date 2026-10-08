"""Punto de entrada de la API (D3). Sin variable ``app`` a nivel de módulo."""
from fastapi import FastAPI
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.errores import registrar_manejadores
from app.api.routers import turnos
from app.infrastructure.db.modelos import Base
from app.infrastructure.db.motor import crear_engine_en_memoria
from app.infrastructure.db.seed_demo import cargar_demo


def crear_app(engine: Engine) -> FastAPI:
    """Aplicación sobre el engine dado; la usan los tests de API con el engine del test."""
    app = FastAPI(title="Turnos Odontológicos AR")
    app.state.fabrica_sesiones = sessionmaker(bind=engine, expire_on_commit=False)
    app.include_router(turnos.router)
    registrar_manejadores(app)
    return app


def crear_app_demo() -> FastAPI:
    """Aplicación para probar a mano en ``/docs``: base en memoria con el seed de D19.

    Fábrica sin argumentos, para ``python -m uvicorn app.main:crear_app_demo --factory``.
    """
    engine = crear_engine_en_memoria()
    Base.metadata.create_all(engine)
    with Session(engine) as sesion:
        cargar_demo(sesion)
    return crear_app(engine)
