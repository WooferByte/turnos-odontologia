"""Dependencias de la API (D12): la unidad de trabajo, el reloj y las piezas de la sesión."""
from fastapi import Request

from app.application.puertos import FirmadorDeTokens, HasherDeContrasenas
from app.application.sesion import Vigencias
from app.domain.tiempo import Reloj, utc_now
from app.infrastructure.unidad_de_trabajo import UnidadDeTrabajoSqlAlchemy


def get_uow(request: Request) -> UnidadDeTrabajoSqlAlchemy:
    """Una unidad de trabajo nueva por petición, sobre la fábrica de sesiones de la app."""
    return UnidadDeTrabajoSqlAlchemy(request.app.state.fabrica_sesiones)


def get_reloj() -> Reloj:
    return utc_now


def get_firmador(request: Request) -> FirmadorDeTokens:
    return request.app.state.firmador


def get_hasher(request: Request) -> HasherDeContrasenas:
    return request.app.state.hasher


def get_vigencias(request: Request) -> Vigencias:
    return request.app.state.vigencias
