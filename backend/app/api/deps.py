"""Dependencias de la API (D12): la unidad de trabajo y el reloj."""
from fastapi import Request

from app.domain.tiempo import Reloj, utc_now
from app.infrastructure.unidad_de_trabajo import UnidadDeTrabajoSqlAlchemy


def get_uow(request: Request) -> UnidadDeTrabajoSqlAlchemy:
    """Una unidad de trabajo nueva por petición, sobre la fábrica de sesiones de la app."""
    return UnidadDeTrabajoSqlAlchemy(request.app.state.fabrica_sesiones)


def get_reloj() -> Reloj:
    return utc_now
