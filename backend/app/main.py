"""Punto de entrada de la API (D3). Sin variable ``app`` a nivel de módulo."""
import os
from collections.abc import Mapping

from fastapi import FastAPI
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.errores import registrar_manejadores
from app.api.routers import prestaciones, sillones, turnos
from app.infrastructure.db.modelos import Base
from app.infrastructure.configuracion import leer_database_url
from app.infrastructure.db.motor import crear_engine, crear_engine_en_memoria
from app.infrastructure.db.seed_demo import cargar_demo


def crear_app(engine: Engine) -> FastAPI:
    """Aplicación sobre el engine dado; la usan los tests de API con el engine del test."""
    app = FastAPI(title="Turnos Odontológicos AR")
    app.state.fabrica_sesiones = sessionmaker(bind=engine, expire_on_commit=False)
    app.include_router(turnos.router)
    app.include_router(prestaciones.router)
    app.include_router(sillones.router)
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


def crear_app_desde_entorno(entorno: Mapping[str, str] = os.environ) -> FastAPI:
    """Aplicación sobre la base de ``DATABASE_URL`` (design I12); la arranca Compose.

    No migra ni carga datos: eso lo hace el comando de arranque del contenedor. Si falta la
    variable levanta ``ConfiguracionInvalida``: no cae en silencio a una base en memoria.
    Fábrica para ``uvicorn app.main:crear_app_desde_entorno --factory``.
    """
    return crear_app(crear_engine(leer_database_url(entorno)))
