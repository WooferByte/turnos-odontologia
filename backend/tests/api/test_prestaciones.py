"""``/prestaciones`` por HTTP con ``TestClient`` sobre ``crear_app(engine)`` (US-001 CA-1 a CA-3).

Sin dobles: la sesión y los repositorios son los reales, sobre el engine SQLite del test.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import crear_app
from tests.factories import un_consultorio, una_prestacion

CAMPOS_DE_PRESTACION_SALIDA = {"id", "nombre", "duracion_minutos", "color", "reservable_online", "activa"}
PROBLEMA_JSON = "application/problem+json"


@pytest.fixture
def cliente(engine) -> TestClient:
    return TestClient(crear_app(engine))


def test_ca1_post_prestaciones_responde_201_con_los_seis_campos(cliente, sesion):
    un_consultorio(sesion)

    respuesta = cliente.post(
        "/prestaciones", json={"nombre": "Blanqueamiento", "duracion_minutos": 60, "color": "#3A7BD5"}
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert set(cuerpo) == CAMPOS_DE_PRESTACION_SALIDA
    assert cuerpo["id"] >= 1
    assert {k: v for k, v in cuerpo.items() if k != "id"} == {
        "nombre": "Blanqueamiento",
        "duracion_minutos": 60,
        "color": "#3A7BD5",
        "reservable_online": False,
        "activa": True,
    }


def test_ca1_post_prestaciones_guarda_sin_espacios_de_mas_y_acepta_reservable_online(cliente, sesion):
    un_consultorio(sesion)

    respuesta = cliente.post(
        "/prestaciones",
        json={
            "nombre": "  Control   de ortodoncia ",
            "duracion_minutos": 45,
            "color": "#43a047",
            "reservable_online": True,
        },
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["nombre"] == "Control de ortodoncia"
    assert cuerpo["color"] == "#43a047"  # se guarda tal como llega
    assert cuerpo["reservable_online"] is True


def test_ca1_get_prestaciones_lista_activas_e_inactivas_por_id(cliente, sesion):
    consultorio = un_consultorio(sesion)
    activa = una_prestacion(sesion, consultorio, nombre="Limpieza", color="#43A047")
    inactiva = una_prestacion(sesion, consultorio, nombre="Obturación", activa=False)

    respuesta = cliente.get("/prestaciones")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert [(p["id"], p["nombre"], p["activa"]) for p in cuerpo] == [
        (activa.id, "Limpieza", True),
        (inactiva.id, "Obturación", False),
    ]
    assert all(set(p) == CAMPOS_DE_PRESTACION_SALIDA for p in cuerpo)
    assert cuerpo[0]["color"] == "#43A047"


def test_ca1_get_prestaciones_sin_ninguna_responde_lista_vacia(cliente, sesion):
    un_consultorio(sesion)

    respuesta = cliente.get("/prestaciones")

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_ca1_post_con_nombre_repetido_responde_409_con_rn_ag_15(cliente, sesion):
    consultorio = un_consultorio(sesion)
    una_prestacion(sesion, consultorio, nombre="Limpieza")

    respuesta = cliente.post(
        "/prestaciones", json={"nombre": "limpieza", "duracion_minutos": 45, "color": "#43A047"}
    )

    assert respuesta.status_code == 409
    assert respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-AG-15"]
    assert "«Limpieza»" in cuerpo["detail"]  # el nombre guardado de la existente
    assert len(cliente.get("/prestaciones").json()) == 1


def test_ca2_post_con_duracion_47_responde_422_con_rn_ag_01(cliente, sesion):
    un_consultorio(sesion)

    respuesta = cliente.post(
        "/prestaciones", json={"nombre": "Blanqueamiento", "duracion_minutos": 47, "color": "#3A7BD5"}
    )

    assert respuesta.status_code == 422
    assert respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-AG-01"]
    (error,) = cuerpo["errores"]
    assert (error["campo"], error["codigo"]) == ("duracion_minutos", "RN-AG-01")
    assert "múltiplo de 5" in error["mensaje"]
    assert cliente.get("/prestaciones").json() == []


def test_ca1_patch_del_color_responde_200_y_deja_lo_demas_igual(cliente, sesion):
    consultorio = un_consultorio(sesion)
    original = una_prestacion(sesion, consultorio, nombre="Limpieza", duracion_minutos=45)

    respuesta = cliente.patch(f"/prestaciones/{original.id}", json={"color": "#112233"})

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "id": original.id,
        "nombre": "Limpieza",
        "duracion_minutos": 45,
        "color": "#112233",
        "reservable_online": False,
        "activa": True,
    }
    assert cliente.get("/prestaciones").json() == [respuesta.json()]


def test_ca1_patch_de_una_prestacion_inexistente_responde_404_con_rn_gl_04(cliente, sesion):
    un_consultorio(sesion)

    respuesta = cliente.patch("/prestaciones/999", json={"color": "#112233"})

    assert respuesta.status_code == 404
    assert respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-GL-04"]
    assert cuerpo["referencias"] == [
        {"recurso": "prestacion", "recurso_id": 999, "motivo": "inexistente"}
    ]
