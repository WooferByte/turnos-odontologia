"""Reloj y validación de fechas (RN-GL-01, DD-13).

Toda fecha del sistema es aware y está en UTC. Este módulo tiene el único
``datetime.now`` permitido y la única definición de la regla «UTC o nada».
"""
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from app.domain.errors import FechaNoUTC

UTC = timezone.utc
Reloj = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


def exigir_utc(valor: datetime, campo: str) -> None:
    """Levanta ``FechaNoUTC`` si ``valor`` es naive o tiene un desfase distinto de cero."""
    if valor.tzinfo is None or valor.utcoffset() != timedelta(0):
        raise FechaNoUTC(campo)


def a_texto_utc(valor: datetime) -> str:
    """Texto ISO 8601 en UTC con ``Z`` (``2026-11-02T10:00:00Z``); exige UTC (RN-GL-01)."""
    exigir_utc(valor, "fecha")
    return valor.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
