"""El día del consultorio: de medianoche a medianoche locales, en UTC (RN-GL-01, D316). Puro, sin base."""
from datetime import date, datetime, timedelta, timezone

import pytest

from app.domain.agenda.dia import hoy_en, rango_del_dia

BUENOS_AIRES = "America/Argentina/Buenos_Aires"


def utc(texto):
    return datetime.fromisoformat(texto).replace(tzinfo=timezone.utc)


def test_age1b_el_dia_del_consultorio_va_de_medianoche_a_medianoche_local():
    desde, hasta = rango_del_dia(date(2026, 11, 2), BUENOS_AIRES)

    assert desde == utc("2026-11-02T03:00:00")
    assert hasta == utc("2026-11-03T03:00:00")
    assert desde.utcoffset().total_seconds() == 0


def test_age1c_hoy_es_la_fecha_local_del_reloj():
    assert hoy_en(utc("2026-11-03T01:00:00"), BUENOS_AIRES) == date(2026, 11, 2)


@pytest.mark.parametrize(
    ("dia", "desde", "hasta"),
    [
        (date(2026, 11, 1), "2026-11-01T03:00:00", "2026-11-02T03:00:00"),
        (date(2026, 12, 31), "2026-12-31T03:00:00", "2027-01-01T03:00:00"),
    ],
)
def test_age1b_otros_dias_incluido_el_cambio_de_anio(dia, desde, hasta):
    assert rango_del_dia(dia, BUENOS_AIRES) == (utc(desde), utc(hasta))


@pytest.mark.parametrize(
    ("ahora", "esperada"),
    [
        ("2026-11-03T03:00:00", date(2026, 11, 3)),
        ("2026-11-03T02:59:00", date(2026, 11, 2)),
    ],
)
def test_age1c_hoy_cambia_justo_a_la_medianoche_local(ahora, esperada):
    assert hoy_en(utc(ahora), BUENOS_AIRES) == esperada


@pytest.mark.parametrize(
    ("dia", "horas"),
    [(date(2026, 9, 6), 23), (date(2026, 4, 4), 25), (date(2026, 11, 2), 24)],
)
def test_age1b_un_dia_con_cambio_de_hora_dura_lo_que_dura_en_el_consultorio(dia, horas):
    desde, hasta = rango_del_dia(dia, "America/Santiago")

    assert hasta - desde == timedelta(hours=horas)


def test_age1c_un_ahora_naive_se_rechaza():
    with pytest.raises(Exception) as error:
        hoy_en(datetime(2026, 11, 3, 1, 0), BUENOS_AIRES)

    assert type(error.value).__name__ == "FechaNoUTC"


@pytest.mark.parametrize("zona", [BUENOS_AIRES, "Asia/Tokyo", "Pacific/Kiritimati"])
@pytest.mark.parametrize("dia", [date(1, 1, 2), date(9999, 12, 30)])
def test_age3a_los_extremos_aceptados_del_calendario_no_desbordan(dia, zona):
    desde, hasta = rango_del_dia(dia, zona)

    assert hasta - desde == timedelta(days=1)
    assert desde.utcoffset() == timedelta(0)
