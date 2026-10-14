"""``/prestaciones`` por HTTP con ``TestClient`` sobre ``crear_app(engine)`` (US-001 CA-1 a CA-3).

Sin dobles: la sesión y los repositorios son los reales, sobre el engine SQLite del test.
"""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_reloj
from app.infrastructure.db.modelos import TurnoModelo
from app.main import crear_app
from tests.conftest import a_las, reloj_fijo
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
)

CAMPOS_DE_PRESTACION_SALIDA = {"id", "nombre", "duracion_minutos", "color", "reservable_online", "activa"}
PROBLEMA_JSON = "application/problem+json"


@pytest.fixture
def cliente(engine) -> TestClient:
    app = crear_app(engine)
    app.dependency_overrides[get_reloj] = lambda: reloj_fijo
    return TestClient(app)


def _escenario(sesion, duracion_minutos: int) -> dict:
    """Consultorio con un profesional, un sillón y un paciente, y una prestación de esa duración."""
    consultorio = un_consultorio(sesion)
    return {
        "paciente": un_paciente(sesion, consultorio),
        "profesional": un_profesional(sesion, consultorio),
        "sillon": un_sillon(sesion, consultorio),
        "prestacion": una_prestacion(sesion, consultorio, duracion_minutos=duracion_minutos),
    }


def _pedir_turno(cliente, datos: dict, inicio: str):
    return cliente.post(
        "/turnos",
        json={
            "paciente_id": datos["paciente"].id,
            "prestacion_id": datos["prestacion"].id,
            "inicio": inicio,
            "profesional_id": datos["profesional"].id,
            "sillon_id": datos["sillon"].id,
        },
    )


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


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"nombre": "Blanqueamiento", "duracion_minutos": 60, "color": "azul"},
        {"duracion_minutos": 60, "color": "#3A7BD5"},
        {"nombre": "   ", "duracion_minutos": 60, "color": "#3A7BD5"},
        {"nombre": "Blanqueamiento", "duracion_minutos": 60, "color": "#3A7BD5", "activa": False},
    ],
    ids=["color_sin_formato", "sin_nombre", "nombre_en_blanco", "campo_de_mas"],
)
def test_ca1_post_mal_formado_responde_422_sin_codigo(cliente, sesion, cuerpo):
    un_consultorio(sesion)

    respuesta = cliente.post("/prestaciones", json=cuerpo)

    assert respuesta.status_code == 422
    assert respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    assert respuesta.json()["codigos"] == []
    assert cliente.get("/prestaciones").json() == []


@pytest.mark.parametrize(
    ("ruta", "cuerpo"),
    [
        ("/prestaciones/{id}", {"activa": False, "extra": 1}),
        ("/prestaciones/{id}", {"nombre": None}),
        ("/prestaciones/abc", {"color": "#112233"}),
    ],
    ids=["campo_de_mas", "nombre_nulo", "id_no_entero"],
)
def test_ca1_patch_mal_formado_no_cambia_nada(cliente, sesion, ruta, cuerpo):
    consultorio = un_consultorio(sesion)
    original = una_prestacion(sesion, consultorio, nombre="Limpieza")
    antes = cliente.get("/prestaciones").json()

    respuesta = cliente.patch(ruta.format(id=original.id), json=cuerpo)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []
    assert cliente.get("/prestaciones").json() == antes


def test_ca1_patch_con_nombre_nulo_nombra_el_campo(cliente, sesion):
    consultorio = un_consultorio(sesion)
    original = una_prestacion(sesion, consultorio)

    respuesta = cliente.patch(f"/prestaciones/{original.id}", json={"nombre": None})

    assert [e["campo"] for e in respuesta.json()["errores"]] == ["nombre"]


def test_ca1_patch_vacio_responde_200_sin_cambios(cliente, sesion):
    consultorio = un_consultorio(sesion)
    original = una_prestacion(sesion, consultorio, nombre="Limpieza", duracion_minutos=45)
    antes = cliente.get("/prestaciones").json()

    respuesta = cliente.patch(f"/prestaciones/{original.id}", json={})

    assert respuesta.status_code == 200
    assert [respuesta.json()] == antes


def test_ca2_patch_con_duracion_invalida_responde_422(cliente, sesion):
    consultorio = un_consultorio(sesion)
    original = una_prestacion(sesion, consultorio, duracion_minutos=45)

    respuesta = cliente.patch(f"/prestaciones/{original.id}", json={"duracion_minutos": 52})

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-AG-01"]
    assert [e["campo"] for e in cuerpo["errores"]] == ["duracion_minutos"]
    assert "múltiplo de 5" in cuerpo["detail"]
    assert cliente.get("/prestaciones").json()[0]["duracion_minutos"] == 45


def test_openapi_declara_los_errores_de_prestaciones_con_el_esquema_problema(engine):
    openapi = crear_app(engine).openapi()

    esperados = {
        ("/prestaciones", "post"): {"201", "409", "422"},
        ("/prestaciones/{prestacion_id}", "patch"): {"200", "404", "409", "422"},
    }
    for (ruta, metodo), estados in esperados.items():
        respuestas = openapi["paths"][ruta][metodo]["responses"]
        assert estados <= set(respuestas)
        for estado in estados - {"200", "201"}:
            assert respuestas[estado]["content"]["application/problem+json"]["schema"] == {
                "$ref": "#/components/schemas/Problema"
            }
    assert "HTTPValidationError" not in openapi["components"]["schemas"]


def test_ca3_alargar_la_duracion_no_cambia_el_turno_existente(cliente, sesion):
    datos = _escenario(sesion, duracion_minutos=30)
    un_turno(sesion, **{k: datos[k] for k in ("paciente", "profesional", "sillon", "prestacion")}, inicio=a_las(10))

    editada = cliente.patch(f"/prestaciones/{datos['prestacion'].id}", json={"duracion_minutos": 60})
    contiguo = _pedir_turno(cliente, datos, "2026-11-02T10:30:00Z")

    assert editada.status_code == 200
    # El turno de 10:00-10:30 conserva su fin: el contiguo de 10:30 cabe y nace con 60 minutos.
    assert contiguo.status_code == 201
    cuerpo = contiguo.json()
    assert cuerpo["duracion_minutos"] == 60
    assert datetime.fromisoformat(cuerpo["fin"]) == a_las(11, 30)


def test_ca3_acortar_la_duracion_no_libera_el_horario(cliente, sesion):
    datos = _escenario(sesion, duracion_minutos=60)
    un_turno(sesion, **{k: datos[k] for k in ("paciente", "profesional", "sillon", "prestacion")}, inicio=a_las(10))

    editada = cliente.patch(f"/prestaciones/{datos['prestacion'].id}", json={"duracion_minutos": 30})
    solapado = _pedir_turno(cliente, datos, "2026-11-02T10:30:00Z")

    assert editada.status_code == 200
    # El turno de 10:00-11:00 conserva su fin: las 10:30 siguen ocupadas.
    assert solapado.status_code == 409
    assert solapado.json()["codigos"] == ["RN-AG-05", "RN-AG-08"]


def test_ca1_una_prestacion_desactivada_no_admite_turnos_nuevos(cliente, sesion, fabrica_sesiones):
    datos = _escenario(sesion, duracion_minutos=45)
    existente = un_turno(
        sesion, **{k: datos[k] for k in ("paciente", "profesional", "sillon", "prestacion")}, inicio=a_las(10)
    )
    ruta = f"/prestaciones/{datos['prestacion'].id}"

    desactivada = cliente.patch(ruta, json={"activa": False})
    rechazado = _pedir_turno(cliente, datos, "2026-11-02T11:00:00Z")

    assert desactivada.status_code == 200
    assert rechazado.status_code == 422
    cuerpo = rechazado.json()
    assert cuerpo["codigos"] == ["RN-GL-04"]
    assert cuerpo["referencias"] == [
        {"recurso": "prestacion", "recurso_id": datos["prestacion"].id, "motivo": "inactivo"}
    ]
    with fabrica_sesiones() as otra:
        turno = otra.get(TurnoModelo, existente.id)
        assert (turno.inicio, turno.fin, turno.estado) == (existente.inicio, existente.fin, "reservado")
    reactivada = cliente.patch(ruta, json={"activa": True})
    aceptado = _pedir_turno(cliente, datos, "2026-11-02T11:00:00Z")
    assert reactivada.status_code == 200
    assert aceptado.status_code == 201


def test_ca3_editar_la_prestacion_no_agrega_eventos_al_historial(cliente, sesion):
    datos = _escenario(sesion, duracion_minutos=30)
    turno_id = _pedir_turno(cliente, datos, "2026-11-02T10:00:00Z").json()["id"]
    antes = cliente.get(f"/turnos/{turno_id}/historial").json()

    cliente.patch(f"/prestaciones/{datos['prestacion'].id}", json={"duracion_minutos": 60, "activa": False})
    despues = cliente.get(f"/turnos/{turno_id}/historial").json()

    assert len(antes) == 1
    assert despues == antes
