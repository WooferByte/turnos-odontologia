"""El día del consultorio (RN-GL-01, D316): de medianoche a medianoche locales, expresado en UTC.

Precondición: ``fecha`` entre 0001-01-02 y 9999-12-30; la API rechaza los extremos antes de llegar
acá (D322), así que este módulo no trata el desborde de ``datetime``.
"""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.domain.tiempo import UTC, exigir_utc


def rango_del_dia(fecha: date, zona: str) -> tuple[datetime, datetime]:
    """``[medianoche local de fecha, medianoche local del día siguiente)`` como instantes aware en UTC."""
    local = ZoneInfo(zona)
    desde = datetime.combine(fecha, time.min, tzinfo=local)
    hasta = datetime.combine(fecha + timedelta(days=1), time.min, tzinfo=local)
    return desde.astimezone(UTC), hasta.astimezone(UTC)


def hoy_en(ahora_utc: datetime, zona: str) -> date:
    """La fecha local del consultorio en el instante ``ahora_utc`` (aware, UTC)."""
    exigir_utc(ahora_utc, "ahora")
    return ahora_utc.astimezone(ZoneInfo(zona)).date()
