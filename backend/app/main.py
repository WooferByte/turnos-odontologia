"""Punto de entrada de la API (D3). Sin variable ``app`` a nivel de módulo."""
import os
from collections.abc import Mapping
from datetime import timedelta

from fastapi import FastAPI
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.errores import registrar_manejadores
from app.api.routers import auth, prestaciones, sillones, turnos
from app.application.sesion import Vigencias
from app.infrastructure.db.modelos import Base
from app.infrastructure.configuracion import (
    ConfiguracionDeSesion,
    leer_configuracion_de_sesion,
    leer_database_url,
    secreto_efimero,
)
from app.infrastructure.db.motor import crear_engine, crear_engine_en_memoria
from app.infrastructure.db.seed_demo import (
    CONTRASENA_DEMO,
    cargar_demo,
    cargar_recepcionista_demo_si_falta,
    cargar_roles_demo_si_faltan,
    cargar_usuario_demo,
)
from app.infrastructure.seguridad.contrasenas import HasherBcrypt
from app.infrastructure.seguridad.tokens import FirmadorJwtHs256


def crear_app(engine: Engine, sesion: ConfiguracionDeSesion | None = None) -> FastAPI:
    """Aplicación sobre el engine dado; la usan los tests de API con el engine del test.

    Sin ``sesion`` usa un secreto efímero (D196): los tokens mueren con el proceso.
    """
    sesion = sesion or ConfiguracionDeSesion(secreto_efimero())
    app = FastAPI(title="Turnos Odontológicos AR")
    app.state.fabrica_sesiones = sessionmaker(bind=engine, expire_on_commit=False)
    app.state.firmador = FirmadorJwtHs256(sesion.secreto)
    app.state.hasher = HasherBcrypt(sesion.rondas_bcrypt)
    app.state.vigencias = Vigencias(
        access=timedelta(minutes=sesion.minutos_access), refresh=timedelta(days=sesion.dias_refresh)
    )
    app.include_router(auth.router)
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
        hash_password = HasherBcrypt().hashear(CONTRASENA_DEMO)  # una sola vez: los dos usuarios comparten la contraseña
        cargar_usuario_demo(sesion, hash_password)
        cargar_roles_demo_si_faltan(sesion)
        cargar_recepcionista_demo_si_falta(sesion, hash_password)
    return crear_app(engine)


def crear_app_desde_entorno(entorno: Mapping[str, str] = os.environ) -> FastAPI:
    """Aplicación sobre la base de ``DATABASE_URL`` (design I12); la arranca Compose.

    No migra ni carga datos: eso lo hace el comando de arranque del contenedor. Si falta la
    variable levanta ``ConfiguracionInvalida``: no cae en silencio a una base en memoria. Lo mismo
    con ``JWT_SECRET`` ausente o de menos de 32 bytes: nunca usa un secreto efímero (design J10).
    Fábrica para ``uvicorn app.main:crear_app_desde_entorno --factory``.
    """
    url = leer_database_url(entorno)
    sesion = leer_configuracion_de_sesion(entorno)
    return crear_app(crear_engine(url), sesion)
