"""``POST /turnos`` por HTTP con ``TestClient`` sobre ``crear_app(engine)`` (D3, D4, D12, D16).

Sin dobles: la sesión y el repositorio son los reales, sobre el engine SQLite del test. Solo se
sustituye el reloj, con ``app.dependency_overrides[get_reloj]``.
"""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_reloj
from app.main import crear_app
from tests.conftest import RELOJ_FIJO, a_las, reloj_fijo
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
)

CAMPOS_DE_TURNO_SALIDA = {
    "id",
    "consultorio_id",
    "paciente_id",
    "profesional_id",
    "sillon_id",
    "prestacion_id",
    "inicio",
    "fin",
    "duracion_minutos",
    "estado",
    "creado_en",
}


@pytest.fixture
def cliente(engine) -> TestClient:
    app = crear_app(engine)
    app.dependency_overrides[get_reloj] = lambda: reloj_fijo
    return TestClient(app)


def _escenario(sesion, duracion_minutos: int = 30) -> dict:
    consultorio = un_consultorio(sesion)
    return {
        "consultorio": consultorio,
        "paciente": un_paciente(sesion, consultorio),
        "profesional": un_profesional(sesion, consultorio),
        "sillon": un_sillon(sesion, consultorio),
        "prestacion": una_prestacion(sesion, consultorio, duracion_minutos=duracion_minutos),
    }


def _fecha(texto: str) -> datetime:
    return datetime.fromisoformat(texto)


def test_e1_post_turnos_responde_201(cliente, sesion):
    datos = _escenario(sesion, duracion_minutos=30)

    respuesta = cliente.post(
        "/turnos",
        json={
            "paciente_id": datos["paciente"].id,
            "prestacion_id": datos["prestacion"].id,
            "inicio": "2026-11-02T10:00:00Z",
            "profesional_id": datos["profesional"].id,
            "sillon_id": datos["sillon"].id,
        },
    )

    assert respuesta.status_code == 201
    assert respuesta.headers["content-type"] == "application/json"
    cuerpo = respuesta.json()
    assert set(cuerpo) == CAMPOS_DE_TURNO_SALIDA
    assert isinstance(cuerpo["id"], int)
    assert cuerpo["consultorio_id"] == datos["consultorio"].id
    assert cuerpo["paciente_id"] == datos["paciente"].id
    assert cuerpo["profesional_id"] == datos["profesional"].id
    assert cuerpo["sillon_id"] == datos["sillon"].id
    assert cuerpo["prestacion_id"] == datos["prestacion"].id
    assert _fecha(cuerpo["inicio"]) == a_las(10)
    assert _fecha(cuerpo["fin"]) == a_las(10, 30)
    assert cuerpo["duracion_minutos"] == 30
    assert cuerpo["estado"] == "reservado"
    assert _fecha(cuerpo["creado_en"]) == RELOJ_FIJO
    assert _fecha(cuerpo["inicio"]).utcoffset() == timedelta(0)
