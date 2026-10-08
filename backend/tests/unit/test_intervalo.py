"""Value object Intervalo [inicio, fin) (RN-AG-09, RN-AG-10d, E8)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.domain.agenda.intervalo import Intervalo
from app.domain.errors import FechaNoUTC, IntervaloInvalido
from app.domain.tiempo import UTC

INICIO = datetime(2026, 11, 2, 13, 0, tzinfo=UTC)
FIN = datetime(2026, 11, 2, 13, 30, tzinfo=UTC)
MENOS_TRES = timezone(timedelta(hours=-3))


def test_intervalo_valido_guarda_inicio_y_fin():
    intervalo = Intervalo(INICIO, FIN)

    assert intervalo.inicio == INICIO
    assert intervalo.fin == FIN


def test_e8_fecha_naive_en_inicio_levanta_rn_gl_01():
    with pytest.raises(FechaNoUTC) as info:
        Intervalo(datetime(2026, 11, 2, 13, 0), FIN)

    assert info.value.codigo == "RN-GL-01"
    assert info.value.campo == "inicio"


def test_e8_fecha_naive_en_fin_levanta_rn_gl_01():
    with pytest.raises(FechaNoUTC) as info:
        Intervalo(INICIO, datetime(2026, 11, 2, 13, 30))

    assert info.value.codigo == "RN-GL-01"
    assert info.value.campo == "fin"


def test_e8_desfase_menos_tres_levanta_rn_gl_01():
    with pytest.raises(FechaNoUTC) as info:
        Intervalo(datetime(2026, 11, 2, 10, 0, tzinfo=MENOS_TRES), FIN)

    assert info.value.codigo == "RN-GL-01"


def test_e8_inicio_igual_a_fin_levanta_rn_ag_10d():
    with pytest.raises(IntervaloInvalido) as info:
        Intervalo(INICIO, INICIO)

    assert info.value.codigo == "RN-AG-10d"
    assert info.value.codigos == ["RN-AG-10d"]


def test_e8_inicio_posterior_a_fin_levanta_rn_ag_10d():
    with pytest.raises(IntervaloInvalido) as info:
        Intervalo(FIN, INICIO)

    assert info.value.codigo == "RN-AG-10d"


# --- Intervalo.para_turno (RN-AG-02, RN-AG-10d) ---
BUENOS_AIRES = "America/Argentina/Buenos_Aires"


def test_para_turno_dentro_del_dia_local_es_valido():
    # 23:30 UTC + 60 min = 20:30 a 21:30 en Buenos Aires.
    inicio = datetime(2026, 11, 2, 23, 30, tzinfo=UTC)

    intervalo = Intervalo.para_turno(inicio, 60, BUENOS_AIRES)

    assert intervalo.inicio == inicio
    assert intervalo.fin == datetime(2026, 11, 3, 0, 30, tzinfo=UTC)


def test_para_turno_que_cruza_la_medianoche_local_se_rechaza():
    # 02:30 UTC + 60 min = 23:30 a 00:30 en Buenos Aires.
    inicio = datetime(2026, 11, 3, 2, 30, tzinfo=UTC)

    with pytest.raises(IntervaloInvalido) as info:
        Intervalo.para_turno(inicio, 60, BUENOS_AIRES)

    assert info.value.codigo == "RN-AG-10d"


def test_para_turno_que_termina_justo_a_la_medianoche_local_es_valido():
    # 02:30 UTC + 30 min = 23:30 a 00:00 en Buenos Aires.
    inicio = datetime(2026, 11, 3, 2, 30, tzinfo=UTC)

    intervalo = Intervalo.para_turno(inicio, 30, BUENOS_AIRES)

    assert intervalo.fin == datetime(2026, 11, 3, 3, 0, tzinfo=UTC)


@pytest.mark.parametrize("duracion", [30, 45, 60])
def test_para_turno_calcula_fin_como_inicio_mas_duracion(duracion):
    inicio = datetime(2026, 11, 2, 13, 0, tzinfo=UTC)

    intervalo = Intervalo.para_turno(inicio, duracion, BUENOS_AIRES)

    assert intervalo.fin == inicio + timedelta(minutes=duracion)


def test_para_turno_con_inicio_naive_levanta_rn_gl_01():
    with pytest.raises(FechaNoUTC) as info:
        Intervalo.para_turno(datetime(2026, 11, 2, 13, 0), 30, BUENOS_AIRES)

    assert info.value.codigo == "RN-GL-01"
    assert info.value.campo == "inicio"


# --- Intervalo.se_solapa_con (RN-AG-09, E5, E7) ---
BASE = Intervalo(datetime(2026, 11, 2, 13, 0, tzinfo=UTC), datetime(2026, 11, 2, 13, 30, tzinfo=UTC))


def _intervalo(hora_inicio: int, minuto_inicio: int, hora_fin: int, minuto_fin: int) -> Intervalo:
    return Intervalo(
        datetime(2026, 11, 2, hora_inicio, minuto_inicio, tzinfo=UTC),
        datetime(2026, 11, 2, hora_fin, minuto_fin, tzinfo=UTC),
    )


@pytest.mark.parametrize(
    ("otro", "esperado"),
    [
        pytest.param(_intervalo(13, 30, 14, 0), False, id="contiguo_despues"),
        pytest.param(_intervalo(12, 30, 13, 0), False, id="contiguo_antes"),
        pytest.param(_intervalo(13, 29, 13, 59), True, id="un_minuto_de_solape"),
        pytest.param(_intervalo(13, 5, 13, 25), True, id="contenido"),
        pytest.param(_intervalo(12, 30, 14, 0), True, id="que_contiene"),
        pytest.param(_intervalo(13, 0, 13, 30), True, id="identico"),
        pytest.param(_intervalo(15, 0, 15, 30), False, id="disjunto"),
    ],
)
def test_se_solapa_con(otro, esperado):
    assert BASE.se_solapa_con(otro) is esperado
    assert otro.se_solapa_con(BASE) is esperado  # la relación es simétrica
