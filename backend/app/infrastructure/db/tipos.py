"""Tipo de columna para fechas: siempre aware y en UTC (RN-GL-01, DD-13, D13)."""
from datetime import datetime, timedelta

from sqlalchemy import DateTime
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator

from app.domain.tiempo import UTC


class FechaHoraUTC(TypeDecorator[datetime]):
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, valor: datetime | None, dialect: Dialect) -> datetime | None:
        if valor is None:
            return None
        if valor.tzinfo is None or valor.utcoffset() != timedelta(0):
            raise ValueError(
                f"Se esperaba una fecha aware en UTC y llegó {valor.isoformat()}; "
                "es un error de programación: el dominio debe validarla antes."
            )
        return valor

    def process_result_value(self, valor: datetime | None, dialect: Dialect) -> datetime | None:
        if valor is None:
            return None
        if valor.tzinfo is None:  # SQLite devuelve naive; solo se escribió UTC
            return valor.replace(tzinfo=UTC)
        return valor.astimezone(UTC)
