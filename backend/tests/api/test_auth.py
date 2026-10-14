"""``/auth/login`` y ``/auth/refresh`` por HTTP con ``TestClient`` sobre ``crear_app(engine, sesion)`` (US-090, US-094).

Sin dobles: sesión, repositorios, hasher y firmador son los reales; solo el reloj se sustituye.
"""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_reloj
from app.infrastructure.configuracion import ConfiguracionDeSesion
from app.main import crear_app
from tests.conftest import RELOJ_FIJO, SECRETO_DE_PRUEBA
from tests.factories import CONTRASENA_DE_PRUEBA, un_consultorio, un_usuario

PROBLEMA_JSON = "application/problem+json"


class RelojDePrueba:
    """Reloj mutable e inyectable: el test lo mueve entre el inicio de sesión y la renovación."""

    def __init__(self) -> None:
        self.ahora = RELOJ_FIJO

    def __call__(self) -> datetime:
        return self.ahora


@pytest.fixture
def reloj() -> RelojDePrueba:
    return RelojDePrueba()


@pytest.fixture
def cliente(engine, reloj) -> TestClient:
    app = crear_app(engine, ConfiguracionDeSesion(SECRETO_DE_PRUEBA, rondas_bcrypt=4))
    app.dependency_overrides[get_reloj] = lambda: reloj
    return TestClient(app)


def _login(cliente, email: str, contrasena: str = CONTRASENA_DE_PRUEBA):
    return cliente.post("/auth/login", json={"email": email, "contrasena": contrasena})


def _refresh(cliente, token: str):
    return cliente.post("/auth/refresh", json={"refresh_token": token})


def test_us090_ca1_login_valido_responde_200_con_dos_tokens(cliente, sesion):
    usuario = un_usuario(sesion, un_consultorio(sesion))

    respuesta = _login(cliente, usuario.email)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"access_token", "refresh_token", "token_type", "expires_in"}
    assert (cuerpo["token_type"], cuerpo["expires_in"]) == ("bearer", 900)
    assert cuerpo["access_token"] != cuerpo["refresh_token"]
    assert respuesta.headers["cache-control"] == "no-store"


def test_us090_ca2_los_tres_rechazos_del_login_son_el_mismo_401(cliente, sesion):
    consultorio = un_consultorio(sesion)
    activo = un_usuario(sesion, consultorio)
    inactivo = un_usuario(sesion, consultorio, activo=False)

    respuestas = [
        _login(cliente, "nadie@consultorio-demo.test"),
        _login(cliente, activo.email, "otra-contrasena-ficticia"),
        _login(cliente, inactivo.email),
    ]

    for respuesta in respuestas:
        assert respuesta.status_code == 401
        assert respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
        assert respuesta.headers["www-authenticate"] == "Bearer"
        assert respuesta.json()["codigos"] == ["RN-AU-04"]
    assert respuestas[0].json() == respuestas[1].json() == respuestas[2].json()


def test_us094_ca1_refresh_valido_responde_200_sin_refresh_token(cliente, sesion, reloj):
    usuario = un_usuario(sesion, un_consultorio(sesion))
    refresh = _login(cliente, usuario.email).json()["refresh_token"]
    reloj.ahora = RELOJ_FIJO + timedelta(hours=1)

    respuesta = _refresh(cliente, refresh)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"access_token", "token_type", "expires_in"}
    assert (cuerpo["token_type"], cuerpo["expires_in"]) == ("bearer", 900)
    assert respuesta.headers["cache-control"] == "no-store"


def test_us094_ca2_los_rechazos_del_refresh_son_el_mismo_401(cliente, sesion, reloj):
    usuario = un_usuario(sesion, un_consultorio(sesion))
    tokens = _login(cliente, usuario.email).json()
    reloj.ahora = RELOJ_FIJO + timedelta(days=7)  # el instante exacto del vencimiento

    respuestas = [
        _refresh(cliente, tokens["refresh_token"]),  # vencido
        _refresh(cliente, tokens["access_token"]),  # de otro tipo
        _refresh(cliente, "abc"),  # no es un JWT
    ]

    for respuesta in respuestas:
        assert respuesta.status_code == 401
        assert respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
        assert respuesta.headers["www-authenticate"] == "Bearer"
        assert respuesta.json()["codigos"] == ["RN-AU-03"]
    assert respuestas[0].json() == respuestas[1].json() == respuestas[2].json()


def test_us094_ca3_refresh_con_token_version_cambiada_responde_401(cliente, sesion):
    usuario = un_usuario(sesion, un_consultorio(sesion))
    refresh = _login(cliente, usuario.email).json()["refresh_token"]
    usuario.token_version += 1
    sesion.commit()

    respuesta = _refresh(cliente, refresh)

    assert respuesta.status_code == 401
    assert respuesta.json()["codigos"] == ["RN-AU-03"]


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"email": "odontologa@consultorio-demo.test"},
        {"email": "odontologa@consultorio-demo.test", "contrasena": ""},
        {"email": "odontologa@consultorio-demo.test", "contrasena": "x", "recordarme": True},
        {"email": 123, "contrasena": "x"},
        {"email": "", "contrasena": "x"},
    ],
    ids=["sin_contrasena", "contrasena_vacia", "campo_de_mas", "email_numerico", "email_vacio"],
)
def test_us090_ca1_login_mal_formado_responde_422_sin_codigo(cliente, cuerpo):
    respuesta = cliente.post("/auth/login", json=cuerpo)

    assert respuesta.status_code == 422
    assert respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    assert respuesta.json()["codigos"] == []
    assert "www-authenticate" not in respuesta.headers


def test_us090_ca1_login_con_json_roto_responde_422_sin_codigo(cliente):
    respuesta = cliente.post("/auth/login", content="{no es json", headers={"content-type": "application/json"})

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []


@pytest.mark.parametrize("cuerpo", [{}, {"refresh_token": ""}], ids=["sin_refresh_token", "refresh_token_vacio"])
def test_us094_ca2_refresh_mal_formado_responde_422_sin_codigo(cliente, cuerpo):
    respuesta = cliente.post("/auth/refresh", json=cuerpo)

    assert respuesta.status_code == 422
    assert respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    assert respuesta.json()["codigos"] == []


@pytest.mark.parametrize("ruta", ["/auth/login", "/auth/refresh"])
def test_openapi_declara_401_y_422_de_auth_con_el_esquema_problema(cliente, ruta):
    respuestas = cliente.get("/openapi.json").json()["paths"][ruta]["post"]["responses"]

    for estado in ("401", "422"):
        esquema = respuestas[estado]["content"]["application/problem+json"]["schema"]
        assert esquema == {"$ref": "#/components/schemas/Problema"}
