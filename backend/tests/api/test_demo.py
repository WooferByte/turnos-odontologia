"""La demo de Swagger (D3, D19, D124): ``crear_app_demo()`` con el seed de datos ficticios.

Sin dobles: la aplicación, la base en memoria y el seed son los reales. Estos tests no usan el
``engine`` ni las factories de ``conftest.py``: la demo arma su propia base.
"""
from datetime import datetime

from fastapi.testclient import TestClient

from app.main import crear_app_demo

PETICION_DE_EJEMPLO = {"paciente_id": 1, "prestacion_id": 1, "inicio": "2026-11-02T13:00:00Z"}


def _fecha(texto: str) -> datetime:
    return datetime.fromisoformat(texto)


def test_la_peticion_de_ejemplo_del_readme_responde_201():
    cliente = TestClient(crear_app_demo())

    primera = cliente.post("/turnos", json=PETICION_DE_EJEMPLO)
    repetida = cliente.post("/turnos", json=PETICION_DE_EJEMPLO)

    # Paso 1 del recorrido: 201 con el único profesional y el único sillón (RN-AG-14).
    assert primera.status_code == 201
    turno = primera.json()
    assert turno["id"] == 1
    assert turno["consultorio_id"] == 1
    assert turno["paciente_id"] == 1
    assert turno["profesional_id"] == 1
    assert turno["sillon_id"] == 1
    assert turno["prestacion_id"] == 1
    assert turno["duracion_minutos"] == 30
    assert turno["estado"] == "reservado"
    assert _fecha(turno["inicio"]) == _fecha("2026-11-02T13:00:00+00:00")
    assert _fecha(turno["fin"]) == _fecha("2026-11-02T13:30:00+00:00")
    # Paso 2: repetirla choca con el profesional y con el sillón (E4).
    assert repetida.status_code == 409
    assert repetida.json()["codigos"] == ["RN-AG-05", "RN-AG-08"]
