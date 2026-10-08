"""Ida y vuelta de fechas aware en UTC con SQLite (RN-GL-01, D85, D13)."""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, StatementError

from app.domain.tiempo import UTC
from app.infrastructure.db.modelos import TurnoModelo
from tests.conftest import RELOJ_FIJO
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
)

INICIO = datetime(2026, 11, 2, 13, 0, tzinfo=UTC)


def _escenario(sesion):
    consultorio = un_consultorio(sesion)
    return {
        "paciente": un_paciente(sesion, consultorio),
        "profesional": un_profesional(sesion, consultorio),
        "sillon": un_sillon(sesion, consultorio),
        "prestacion": una_prestacion(sesion, consultorio),
    }


def test_turno_guardado_con_inicio_utc_se_lee_con_zona_utc_y_mismo_instante(sesion, fabrica_sesiones):
    turno = un_turno(sesion, inicio=INICIO, **_escenario(sesion))

    with fabrica_sesiones() as otra_sesion:  # sesión nueva: lee de la base, no del caché
        leido = otra_sesion.get(TurnoModelo, turno.id)

    assert leido.inicio.tzinfo is not None
    assert leido.inicio.utcoffset() == timedelta(0)
    assert leido.inicio == INICIO
    assert leido.fin == INICIO + timedelta(minutes=30)


def test_instante_con_otro_desfase_no_se_guarda(sesion):
    datos = _escenario(sesion)
    menos_tres = datetime(2026, 11, 2, 10, 0, tzinfo=timezone(timedelta(hours=-3)))

    with pytest.raises(StatementError) as info:
        un_turno(sesion, inicio=menos_tres, **datos)

    assert isinstance(info.value.orig, ValueError)


def test_guardar_un_datetime_naive_levanta_value_error(sesion):
    datos = _escenario(sesion)

    with pytest.raises(StatementError) as info:
        un_turno(sesion, inicio=datetime(2026, 11, 2, 13, 0), **datos)

    assert isinstance(info.value.orig, ValueError)


def test_consulta_por_rango_con_parametro_aware_devuelve_el_turno_esperado(sesion):
    datos = _escenario(sesion)
    esperado = un_turno(sesion, inicio=INICIO, **datos)
    un_turno(sesion, inicio=INICIO + timedelta(days=1), **datos)  # otro día: queda afuera

    consulta = select(TurnoModelo).where(
        TurnoModelo.inicio < INICIO + timedelta(minutes=15),
        TurnoModelo.fin > INICIO - timedelta(minutes=15),
    )
    encontrados = sesion.scalars(consulta).all()

    assert [t.id for t in encontrados] == [esperado.id]


def test_consulta_por_rango_no_devuelve_turnos_contiguos(sesion):
    datos = _escenario(sesion)
    un_turno(sesion, inicio=INICIO, **datos)  # 13:00-13:30

    consulta = select(TurnoModelo).where(
        TurnoModelo.inicio < INICIO + timedelta(minutes=60),
        TurnoModelo.fin > INICIO + timedelta(minutes=30),  # pide desde las 13:30
    )

    assert sesion.scalars(consulta).all() == []


def test_creado_en_se_lee_con_zona_utc_y_mismo_instante(sesion, fabrica_sesiones):
    turno = un_turno(sesion, inicio=INICIO, **_escenario(sesion))

    with fabrica_sesiones() as otra_sesion:
        leido = otra_sesion.get(TurnoModelo, turno.id)

    assert leido.creado_en.utcoffset() == timedelta(0)
    assert leido.creado_en == RELOJ_FIJO


@pytest.mark.parametrize("desplazamiento_fin", [timedelta(0), timedelta(minutes=-15)])
def test_el_esquema_rechaza_inicio_mayor_o_igual_a_fin(sesion, desplazamiento_fin):
    datos = _escenario(sesion)

    with pytest.raises(IntegrityError):
        un_turno(sesion, inicio=INICIO, fin=INICIO + desplazamiento_fin, **datos)
