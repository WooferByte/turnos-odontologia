"""Caso de uso ``crear_turno`` con repositorio real sobre SQLite en memoria (D12, D16)."""
from datetime import datetime

import pytest
from sqlalchemy import select

from app.application.crear_turno import CrearTurnoComando, crear_turno
from app.domain.errors import Conflicto, ErrorDeSolapamiento, IntervaloInvalido
from app.domain.tiempo import UTC
from app.domain.turnos.estados import EstadoTurno
from app.infrastructure.db.modelos import TurnoModelo
from tests.conftest import RELOJ_FIJO, reloj_fijo
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
)

DIA = (2026, 11, 2)


def _a_las(hora: int, minuto: int = 0) -> datetime:
    return datetime(*DIA, hora, minuto, tzinfo=UTC)


def _escenario(sesion, duracion_minutos: int = 30) -> dict:
    consultorio = un_consultorio(sesion)
    return {
        "consultorio": consultorio,
        "paciente": un_paciente(sesion, consultorio),
        "profesional": un_profesional(sesion, consultorio),
        "sillon": un_sillon(sesion, consultorio),
        "prestacion": una_prestacion(sesion, consultorio, duracion_minutos=duracion_minutos),
    }


def _comando(datos: dict, inicio: datetime) -> CrearTurnoComando:
    return CrearTurnoComando(
        paciente_id=datos["paciente"].id,
        prestacion_id=datos["prestacion"].id,
        inicio=inicio,
        profesional_id=datos["profesional"].id,
        sillon_id=datos["sillon"].id,
    )


def test_e1_feliz_crea_turno_reservado_con_fin_calculado(sesion, fabrica_sesiones, uow):
    datos = _escenario(sesion, duracion_minutos=30)

    turno = crear_turno(_comando(datos, _a_las(10)), uow, reloj_fijo)

    assert turno.id is not None
    assert turno.estado == EstadoTurno.RESERVADO
    assert turno.inicio == _a_las(10)
    assert turno.fin == _a_las(10, 30)
    assert turno.duracion_minutos == 30
    assert turno.consultorio_id == datos["profesional"].consultorio_id
    assert turno.creado_en == RELOJ_FIJO
    with fabrica_sesiones() as otra_sesion:  # sesión nueva: lo que quedó confirmado en la base
        guardado = otra_sesion.get(TurnoModelo, turno.id)
    assert guardado is not None
    assert guardado.estado == "reservado"
    assert guardado.inicio == _a_las(10)
    assert guardado.fin == _a_las(10, 30)
    assert guardado.consultorio_id == datos["consultorio"].id
    assert guardado.profesional_id == datos["profesional"].id
    assert guardado.sillon_id == datos["sillon"].id
    assert guardado.creado_en == RELOJ_FIJO


@pytest.mark.parametrize(
    ("duracion_minutos", "fin_esperado"),
    [(30, _a_las(10, 30)), (45, _a_las(10, 45)), (60, _a_las(11))],
)
def test_e1_fin_es_inicio_mas_la_duracion_de_la_prestacion(
    sesion, fabrica_sesiones, uow, duracion_minutos, fin_esperado
):
    datos = _escenario(sesion, duracion_minutos=duracion_minutos)

    turno = crear_turno(_comando(datos, _a_las(10)), uow, reloj_fijo)

    assert turno.fin == fin_esperado
    assert turno.duracion_minutos == duracion_minutos
    with fabrica_sesiones() as otra_sesion:
        assert otra_sesion.get(TurnoModelo, turno.id).fin == fin_esperado


def test_e1_si_el_caso_de_uso_falla_no_queda_ningun_turno(sesion, fabrica_sesiones, uow):
    datos = _escenario(sesion, duracion_minutos=30)
    cruza_la_medianoche = datetime(2026, 11, 3, 2, 45, tzinfo=UTC)  # 23:45 a 00:15 en Buenos Aires

    with pytest.raises(IntervaloInvalido):
        crear_turno(_comando(datos, cruza_la_medianoche), uow, reloj_fijo)

    with fabrica_sesiones() as otra_sesion:
        assert otra_sesion.scalars(select(TurnoModelo)).all() == []


@pytest.mark.parametrize(
    ("hora", "minuto", "duracion_minutos"),
    [
        pytest.param(10, 15, 30, id="solape-parcial"),
        pytest.param(10, 0, 30, id="identico"),
        pytest.param(10, 10, 15, id="contenido"),
        pytest.param(9, 45, 60, id="contiene-al-existente"),
    ],
)
def test_e2_profesional_ocupado_rechaza_con_rn_ag_05(
    sesion, fabrica_sesiones, uow, hora, minuto, duracion_minutos
):
    datos = _escenario(sesion, duracion_minutos=30)
    prestacion_pedida = una_prestacion(
        sesion, datos["consultorio"], duracion_minutos=duracion_minutos
    )
    sillon_2 = un_sillon(sesion, datos["consultorio"])
    existente = un_turno(
        sesion,
        paciente=datos["paciente"],
        profesional=datos["profesional"],
        sillon=datos["sillon"],
        prestacion=datos["prestacion"],
        inicio=_a_las(10),
    )
    comando = CrearTurnoComando(
        paciente_id=datos["paciente"].id,
        prestacion_id=prestacion_pedida.id,
        inicio=_a_las(hora, minuto),
        profesional_id=datos["profesional"].id,
        sillon_id=sillon_2.id,
    )

    with pytest.raises(ErrorDeSolapamiento) as excinfo:
        crear_turno(comando, uow, reloj_fijo)

    assert excinfo.value.codigos == ["RN-AG-05"]
    assert excinfo.value.conflictos == (
        Conflicto(
            codigo="RN-AG-05",
            recurso="profesional",
            recurso_id=datos["profesional"].id,
            turno_id=existente.id,
        ),
    )
    with fabrica_sesiones() as otra_sesion:
        assert len(otra_sesion.scalars(select(TurnoModelo)).all()) == 1  # solo el existente
