"""``/sillones`` por HTTP con ``TestClient`` sobre ``crear_app(engine)`` (US-004 CA-3).

Sin dobles: la sesión y los repositorios son los reales, sobre el engine SQLite del test.
"""
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_reloj
from app.main import crear_app
from tests.conftest import reloj_fijo
from tests.factories import un_consultorio, un_sillon

CAMPOS_DE_SILLON_SALIDA = {"id", "nombre", "activo"}
PROBLEMA_JSON = "application/problem+json"


@pytest.fixture
def cliente(engine) -> TestClient:
    app = crear_app(engine)
    app.dependency_overrides[get_reloj] = lambda: reloj_fijo
    return TestClient(app)


def test_ca3_post_sillones_responde_201_con_id_nombre_y_activo(cliente, sesion):
    un_consultorio(sesion)

    respuesta = cliente.post("/sillones", json={"nombre": "Sillón 2"})

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert set(cuerpo) == CAMPOS_DE_SILLON_SALIDA
    assert cuerpo["id"] >= 1
    assert (cuerpo["nombre"], cuerpo["activo"]) == ("Sillón 2", True)


def test_ca3_post_sillones_guarda_el_nombre_sin_espacios_de_mas(cliente, sesion):
    un_consultorio(sesion)

    respuesta = cliente.post("/sillones", json={"nombre": "  Box   de cirugía "})

    assert respuesta.status_code == 201
    assert respuesta.json()["nombre"] == "Box de cirugía"
    assert cliente.get("/sillones").json()[0]["nombre"] == "Box de cirugía"


def test_ca3_get_sillones_lista_activos_e_inactivos_por_id(cliente, sesion):
    consultorio = un_consultorio(sesion)
    primero = un_sillon(sesion, consultorio, nombre="Sillón 1")
    segundo = un_sillon(sesion, consultorio, nombre="Sillón 2", activo=False)

    respuesta = cliente.get("/sillones")

    assert respuesta.status_code == 200
    assert respuesta.json() == [
        {"id": primero.id, "nombre": "Sillón 1", "activo": True},
        {"id": segundo.id, "nombre": "Sillón 2", "activo": False},
    ]


def test_ca3_get_sillones_sin_sillones_responde_lista_vacia(cliente, sesion):
    un_consultorio(sesion)

    respuesta = cliente.get("/sillones")

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_ca3_patch_del_nombre_conserva_activo(cliente, sesion):
    sillon = un_sillon(sesion, un_consultorio(sesion), nombre="Sillón 1")

    respuesta = cliente.patch(f"/sillones/{sillon.id}", json={"nombre": "Box 1"})

    assert respuesta.status_code == 200
    assert respuesta.json() == {"id": sillon.id, "nombre": "Box 1", "activo": True}


def test_ca3_patch_activo_false_desactiva_el_sillon(cliente, sesion):
    sillon = un_sillon(sesion, un_consultorio(sesion), nombre="Sillón 1")

    respuesta = cliente.patch(f"/sillones/{sillon.id}", json={"activo": False})

    assert respuesta.status_code == 200
    assert respuesta.json() == {"id": sillon.id, "nombre": "Sillón 1", "activo": False}
    assert cliente.get("/sillones").json()[0]["activo"] is False


def test_ca3_patch_de_sillon_inexistente_responde_404_con_rn_gl_04(cliente, sesion):
    un_consultorio(sesion)

    respuesta = cliente.patch("/sillones/999", json={"nombre": "Fantasma"})

    assert respuesta.status_code == 404
    assert respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-GL-04"]
    assert cuerpo["referencias"] == [{"recurso": "sillon", "recurso_id": 999, "motivo": "inexistente"}]
    assert cuerpo["instance"] == "/sillones/999"
