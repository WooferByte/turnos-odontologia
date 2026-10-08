"""Punto de entrada de la API (D3). Sin variable ``app`` a nivel de módulo."""
from fastapi import FastAPI
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from app.api.errores import registrar_manejadores
from app.api.routers import turnos


def crear_app(engine: Engine) -> FastAPI:
    """Aplicación sobre el engine dado; la usan los tests de API con el engine del test."""
    app = FastAPI(title="Turnos Odontológicos AR")
    app.state.fabrica_sesiones = sessionmaker(bind=engine, expire_on_commit=False)
    app.include_router(turnos.router)
    registrar_manejadores(app)
    return app
