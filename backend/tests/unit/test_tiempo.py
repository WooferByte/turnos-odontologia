"""Reloj y validación de fechas UTC (RN-GL-01, DD-13, D128)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.domain.errors import FechaNoUTC
from app.domain.tiempo import UTC, exigir_utc, utc_now


def test_utc_now_devuelve_aware_utc():
    ahora = utc_now()

    assert ahora.tzinfo is not None
    assert ahora.utcoffset() == timedelta(0)
    # Es un instante cercano al real, no un valor fijo.
    assert abs(datetime.now(timezone.utc) - ahora) < timedelta(seconds=5)


@pytest.mark.parametrize("campo", ["inicio", "fin"])
def test_exigir_utc_naive_levanta_fecha_no_utc_con_el_campo(campo):
    with pytest.raises(FechaNoUTC) as info:
        exigir_utc(datetime(2026, 11, 2, 10, 0), campo)

    assert info.value.codigo == "RN-GL-01"
    assert info.value.codigos == ["RN-GL-01"]
    assert info.value.campo == campo
    assert campo in info.value.mensaje


def test_exigir_utc_con_desfase_menos_tres_levanta_fecha_no_utc():
    local = datetime(2026, 11, 2, 10, 0, tzinfo=timezone(timedelta(hours=-3)))

    with pytest.raises(FechaNoUTC) as info:
        exigir_utc(local, "inicio")

    assert info.value.codigo == "RN-GL-01"
    assert info.value.campo == "inicio"


def test_exigir_utc_acepta_aware_utc():
    assert exigir_utc(datetime(2026, 11, 2, 13, 0, tzinfo=UTC), "inicio") is None
