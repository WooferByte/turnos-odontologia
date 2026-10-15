"""``GET /turnos/{id}/historial`` por HTTP con ``TestClient`` sobre ``crear_app(engine)`` (H9, H10).

Sin dobles: sesión y repositorios reales sobre el engine SQLite del test; solo se sustituye el reloj.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.deps import get_reloj
from app.domain.acceso.roles import Rol
from app.infrastructure.configuracion import ConfiguracionDeSesion
from app.infrastructure.db.modelos import UsuarioModelo
from app.main import crear_app
from tests.conftest import SECRETO_DE_PRUEBA, a_las, reloj_fijo, con_token_del_panel, token_de
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
    un_usuario,
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
    app = crear_app(engine, ConfiguracionDeSesion(SECRETO_DE_PRUEBA, rondas_bcrypt=4))
    app.dependency_overrides[get_reloj] = lambda: reloj_fijo
    return con_token_del_panel(TestClient(app), engine)


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
    assert evento["actor_id"] == str(sesion.scalar(select(UsuarioModelo.id)))  # el del token (E9, D159)
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


def test_his1_id_que_no_es_numero_responde_422_sin_codigo(cliente):
    respuesta = cliente.get("/turnos/abc/historial")

    assert respuesta.status_code == 422
    assert respuesta.headers["content-type"] == "application/problem+json"
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == []
    assert cuerpo["detail"] == (
        "La petición tiene 1 problema de entrada: la ruta no tiene el formato esperado."
    )
    assert cuerpo["instance"] == "/turnos/abc/historial"
    assert len(cuerpo["errores"]) == 1
    assert cuerpo["errores"][0]["campo"] == "turno_id"
    assert cuerpo["errores"][0]["codigo"] is None


@pytest.mark.parametrize("metodo", ["POST", "PUT", "PATCH", "DELETE"])
def test_ca1_la_ruta_del_historial_no_admite_modificaciones(cliente, sesion, metodo):
    datos = _escenario(sesion)
    turno_id = cliente.post("/turnos", json=_pedido(datos)).json()["id"]
    antes = cliente.get(f"/turnos/{turno_id}/historial").json()

    respuesta = cliente.request(metodo, f"/turnos/{turno_id}/historial")

    assert respuesta.status_code == 405
    despues = cliente.get(f"/turnos/{turno_id}/historial")
    assert despues.status_code == 200
    assert despues.json() == antes
    assert len(antes) == 1


def test_ca1_get_historial_de_turno_sin_eventos_responde_lista_vacia(cliente, sesion):
    datos = _escenario(sesion)
    turno = un_turno(  # la factory no registra evento: turno anterior a la migración (H14)
        sesion,
        paciente=datos["paciente"],
        profesional=datos["profesional"],
        sillon=datos["sillon"],
        prestacion=datos["prestacion"],
        inicio=a_las(10),
    )

    respuesta = cliente.get(f"/turnos/{turno.id}/historial")

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_openapi_declara_404_y_422_del_historial_con_el_esquema_problema(engine):
    openapi = crear_app(engine).openapi()

    respuestas = openapi["paths"]["/turnos/{turno_id}/historial"]["get"]["responses"]

    assert {"200", "404", "422"} <= set(respuestas)
    for estado in ("404", "422"):
        contenido = respuestas[estado]["content"]
        assert contenido["application/problem+json"]["schema"] == {
            "$ref": "#/components/schemas/Problema"
        }
    assert "HTTPValidationError" not in openapi["components"]["schemas"]


def test_e9_cada_evento_lleva_al_usuario_que_creo_su_turno(cliente, sesion):
    datos = _escenario(sesion)
    odontologa = un_usuario(sesion, datos["consultorio"], roles=(Rol.ODONTOLOGO,))
    recepcionista = un_usuario(sesion, datos["consultorio"], roles=(Rol.RECEPCIONISTA,))
    turnos = {}
    for usuario, hora in ((odontologa, 10), (recepcionista, 11)):
        creado = cliente.post(
            "/turnos",
            json=_pedido(datos, f"2026-11-02T{hora}:00:00Z"),
            headers={"Authorization": f"Bearer {token_de(usuario.id)}"},
        )
        assert creado.status_code == 201
        turnos[usuario.id] = creado.json()["id"]

    for usuario in (odontologa, recepcionista):
        eventos = cliente.get(f"/turnos/{turnos[usuario.id]}/historial").json()
        assert [e["actor_id"] for e in eventos] == [str(usuario.id)]
