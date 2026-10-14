"""``GET /turnos/{id}/historial`` por HTTP con ``TestClient`` sobre ``crear_app(engine)`` (H9, H10).

Sin dobles: sesión y repositorios reales sobre el engine SQLite del test; solo se sustituye el reloj.
"""
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_reloj
from app.main import crear_app
from tests.conftest import reloj_fijo
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
)

CAMPOS_DE_EVENTO_SALIDA = {
    "id",
    "turno_id",
    "tipo",
    "actor_tipo",
    "actor_id",
    "ocurrido_en",
    "antes",
    "despues",
    "motivo",
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


def _pedido(datos: dict, inicio: str = "2026-11-02T10:00:00Z") -> dict:
    return {
        "paciente_id": datos["paciente"].id,
        "prestacion_id": datos["prestacion"].id,
        "inicio": inicio,
        "profesional_id": datos["profesional"].id,
        "sillon_id": datos["sillon"].id,
    }


def test_e9_post_turnos_deja_el_evento_creado_en_el_historial(cliente, sesion):
    datos = _escenario(sesion)
    creado = cliente.post("/turnos", json=_pedido(datos))
    assert creado.status_code == 201
    turno_id = creado.json()["id"]

    respuesta = cliente.get(f"/turnos/{turno_id}/historial")

    assert respuesta.status_code == 200
    eventos = respuesta.json()
    assert len(eventos) == 1
    evento = eventos[0]
    assert set(evento) == CAMPOS_DE_EVENTO_SALIDA
    assert isinstance(evento["id"], int)
    assert evento["turno_id"] == turno_id
    assert evento["tipo"] == "creado"
    assert evento["actor_tipo"] == "usuario"
    assert evento["actor_id"] is None
    assert evento["ocurrido_en"] == "2026-10-07T12:00:00Z"
    assert evento["antes"] is None
    assert evento["motivo"] is None
    assert evento["despues"] == {
        "estado": "reservado",
        "inicio": "2026-11-02T10:00:00Z",
        "fin": "2026-11-02T10:30:00Z",
        "duracion_minutos": 30,
        "paciente_id": datos["paciente"].id,
        "prestacion_id": datos["prestacion"].id,
        "profesional_id": datos["profesional"].id,
        "sillon_id": datos["sillon"].id,
    }


def test_his1_get_historial_de_turno_inexistente_responde_404(cliente):
    respuesta = cliente.get("/turnos/999/historial")

    assert respuesta.status_code == 404
    assert respuesta.headers["content-type"] == "application/problem+json"
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-GL-04"]
    assert cuerpo["referencias"] == [{"recurso": "turno", "recurso_id": 999, "motivo": "inexistente"}]
    assert cuerpo["status"] == 404
    assert cuerpo["instance"] == "/turnos/999/historial"
