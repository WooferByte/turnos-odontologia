"""``GET /auth/yo`` por HTTP con ``TestClient`` sobre ``crear_app(engine)`` (C-50, capability ``usuario-de-la-sesion``).

Sin dobles: sesión, repositorios, hasher y firmador son los reales, con tokens reales de ``POST /auth/login``
(D211); solo el reloj se sustituye. Cada test lleva el ID de su escenario (SES-1a ... SES-3h). Todos los
datos y todas las contraseñas son ficticios (RN-PR-01).
"""
from dataclasses import dataclass
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_reloj
from app.domain.acceso.roles import Rol
from app.infrastructure.configuracion import ConfiguracionDeSesion
from app.infrastructure.db.modelos import ConsultorioModelo, UsuarioModelo
from app.main import crear_app
from tests.conftest import RELOJ_FIJO, SECRETO_DE_PRUEBA, reloj_fijo
from tests.factories import un_consultorio, un_usuario

PROBLEMA_JSON = "application/problem+json"
CONTRASENA = "demo-consultorio-2026"
EMAIL_ODONTOLOGA = "odontologa@consultorio-demo.test"
EMAIL_RECEPCIONISTA = "recepcion@consultorio-demo.test"
EMAIL_DUENO = "administracion@consultorio-demo.test"
EMAIL_COLEGA = "colega@consultorio-demo.test"
EMAIL_SIN_ROLES = "sin-roles@consultorio-demo.test"


@dataclass
class Escenario:
    odontologa: UsuarioModelo  # id 1: odontologo + dueno
    recepcionista: UsuarioModelo  # id 2: recepcionista


@pytest.fixture
def cliente(engine) -> TestClient:
    app = crear_app(engine, ConfiguracionDeSesion(SECRETO_DE_PRUEBA, rondas_bcrypt=4))
    app.dependency_overrides[get_reloj] = lambda: reloj_fijo
    return TestClient(app)


@pytest.fixture
def demo(sesion: Session) -> Escenario:
    consultorio = un_consultorio(sesion)
    odontologa = un_usuario(
        sesion, consultorio, contrasena=CONTRASENA, email=EMAIL_ODONTOLOGA, roles=(Rol.ODONTOLOGO, Rol.DUENO)
    )
    recepcionista = un_usuario(
        sesion, consultorio, contrasena=CONTRASENA, email=EMAIL_RECEPCIONISTA, roles=(Rol.RECEPCIONISTA,)
    )
    assert (odontologa.id, recepcionista.id) == (1, 2)
    return Escenario(odontologa, recepcionista)


def _login(cliente: TestClient, email: str, contrasena: str = CONTRASENA):
    return cliente.post("/auth/login", json={"email": email, "contrasena": contrasena})


def _sesion_de(cliente: TestClient, email: str, contrasena: str = CONTRASENA) -> dict[str, str]:
    respuesta = _login(cliente, email, contrasena)
    assert respuesta.status_code == 200
    return respuesta.json()


def _bearer(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


def _yo(cliente: TestClient, access: str):
    return cliente.get("/auth/yo", headers=_bearer(access))


# --- SES-1: el usuario del token obtiene su email y sus roles ---------------------------------


def test_ses1a_la_odontologa_obtiene_su_email_y_sus_roles(cliente, demo, sesion) -> None:
    de_la_odontologa = _sesion_de(cliente, " Odontologa@Consultorio-Demo.TEST ")
    antes = sesion.scalars(select(UsuarioModelo.token_version).where(UsuarioModelo.id == 1)).one()

    respuesta = _yo(cliente, de_la_odontologa["access_token"])

    assert respuesta.status_code == 200
    assert respuesta.json() == {"email": EMAIL_ODONTOLOGA, "roles": ["odontologo", "dueno"]}
    sesion.expire_all()
    assert sesion.scalars(select(UsuarioModelo.token_version).where(UsuarioModelo.id == 1)).one() == antes
    assert cliente.get("/usuarios", headers=_bearer(de_la_odontologa["access_token"])).status_code == 200


def test_ses2a_la_respuesta_trae_solo_el_email_y_los_roles_sin_cache(cliente, demo, sesion) -> None:
    de_la_odontologa = _sesion_de(cliente, EMAIL_ODONTOLOGA)
    hash_guardado = sesion.get_one(UsuarioModelo, 1).hash_password

    respuesta = _yo(cliente, de_la_odontologa["access_token"])

    assert respuesta.status_code == 200
    assert set(respuesta.json()) == {"email", "roles"}
    assert hash_guardado not in respuesta.text and de_la_odontologa["access_token"] not in respuesta.text
    assert respuesta.headers["cache-control"] == "no-store"
    esquema = cliente.get("/openapi.json").json()
    ok = esquema["paths"]["/auth/yo"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    salida = esquema["components"]["schemas"][ok["$ref"].rsplit("/", 1)[1]]
    assert set(salida["properties"]) == {"email", "roles"}


def _alta(cliente: TestClient, quien: dict[str, str], email: str, roles: list[str]) -> int:
    respuesta = cliente.post(
        "/usuarios",
        json={"email": email, "contrasena": CONTRASENA, "roles": roles},
        headers=_bearer(quien["access_token"]),
    )
    assert respuesta.status_code == 201
    return respuesta.json()["id"]


def _editar(cliente: TestClient, quien: dict[str, str], usuario_id: int, cuerpo: dict):
    return cliente.patch(f"/usuarios/{usuario_id}", json=cuerpo, headers=_bearer(quien["access_token"]))


def test_ses1b_la_recepcionista_y_el_dueno_obtienen_los_suyos(cliente, demo) -> None:
    de_la_odontologa = _sesion_de(cliente, EMAIL_ODONTOLOGA)
    _alta(cliente, de_la_odontologa, EMAIL_DUENO, ["dueno"])
    de_la_recepcionista = _sesion_de(cliente, EMAIL_RECEPCIONISTA)
    del_dueno = _sesion_de(cliente, EMAIL_DUENO)

    primera = _yo(cliente, de_la_recepcionista["access_token"])
    segunda = _yo(cliente, del_dueno["access_token"])

    assert primera.status_code == 200
    assert primera.json() == {"email": EMAIL_RECEPCIONISTA, "roles": ["recepcionista"]}
    assert segunda.status_code == 200
    assert segunda.json() == {"email": EMAIL_DUENO, "roles": ["dueno"]}


def test_ses1c_un_rol_cambiado_se_ve_en_la_peticion_siguiente(cliente, demo) -> None:
    de_la_odontologa = _sesion_de(cliente, EMAIL_ODONTOLOGA)
    de_la_recepcionista = _sesion_de(cliente, EMAIL_RECEPCIONISTA)
    access = de_la_recepcionista["access_token"]
    assert _yo(cliente, access).json()["roles"] == ["recepcionista"]

    assert _editar(cliente, de_la_odontologa, 2, {"roles": ["recepcionista", "dueno"]}).status_code == 200
    con_dueno = _yo(cliente, access)
    assert _editar(cliente, de_la_odontologa, 2, {"roles": ["recepcionista"]}).status_code == 200
    sin_dueno = _yo(cliente, access)

    assert (con_dueno.status_code, con_dueno.json()["roles"]) == (200, ["recepcionista", "dueno"])
    assert (sin_dueno.status_code, sin_dueno.json()["roles"]) == (200, ["recepcionista"])


def test_ses1d_los_roles_salen_en_el_orden_fijo(cliente, demo) -> None:
    de_la_odontologa = _sesion_de(cliente, EMAIL_ODONTOLOGA)
    colega_id = _alta(cliente, de_la_odontologa, EMAIL_COLEGA, ["dueno"])
    assert _editar(cliente, de_la_odontologa, colega_id, {"roles": ["dueno", "odontologo"]}).status_code == 200
    de_la_colega = _sesion_de(cliente, EMAIL_COLEGA)

    respuesta = _yo(cliente, de_la_colega["access_token"])

    assert respuesta.status_code == 200
    assert respuesta.json() == {"email": EMAIL_COLEGA, "roles": ["odontologo", "dueno"]}


# --- SES-3: sin sesión válida responde el 401 de sesión inválida ------------------------------


def _es_el_401_de_sesion_invalida(respuesta) -> bool:
    return (
        respuesta.status_code == 401
        and respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
        and respuesta.headers["www-authenticate"] == "Bearer"
        and respuesta.json()["codigos"] == ["RN-AU-03"]
    )


def test_ses3a_sin_cabecera_responde_401(cliente, demo) -> None:
    respuesta = cliente.get("/auth/yo")

    assert _es_el_401_de_sesion_invalida(respuesta)
    assert EMAIL_ODONTOLOGA not in respuesta.text


def test_ses3b_otro_esquema_responde_401(cliente, demo) -> None:
    respuesta = cliente.get("/auth/yo", headers={"Authorization": "Basic dXN1YXJpbzp4"})

    assert _es_el_401_de_sesion_invalida(respuesta)
    assert respuesta.json() == cliente.get("/auth/yo").json()


def test_ses3c_token_ilegible_responde_401(cliente, demo) -> None:
    respuesta = _yo(cliente, "no-es-un-jwt")

    assert _es_el_401_de_sesion_invalida(respuesta)
    assert respuesta.json() == cliente.get("/auth/yo").json()


def test_ses3d_refresh_como_access_responde_401(cliente, demo) -> None:
    de_la_odontologa = _sesion_de(cliente, EMAIL_ODONTOLOGA)

    respuesta = _yo(cliente, de_la_odontologa["refresh_token"])

    assert _es_el_401_de_sesion_invalida(respuesta)
    assert respuesta.json() == cliente.get("/auth/yo").json()
    assert EMAIL_ODONTOLOGA not in respuesta.text


def _reloj_a(despues: timedelta):
    return lambda: RELOJ_FIJO + despues


def test_ses3e_access_vencido_responde_401(cliente, demo) -> None:
    de_la_odontologa = _sesion_de(cliente, EMAIL_ODONTOLOGA)  # a las 12:00; el access dura 15 minutos
    cliente.app.dependency_overrides[get_reloj] = lambda: _reloj_a(timedelta(minutes=14, seconds=59))
    todavia_vigente = _yo(cliente, de_la_odontologa["access_token"])
    cliente.app.dependency_overrides[get_reloj] = lambda: _reloj_a(timedelta(minutes=15))

    respuesta = _yo(cliente, de_la_odontologa["access_token"])

    assert todavia_vigente.status_code == 200
    assert _es_el_401_de_sesion_invalida(respuesta)
    assert respuesta.json() == cliente.get("/auth/yo").json()
    assert EMAIL_ODONTOLOGA not in respuesta.text


def test_ses3f_un_usuario_desactivado_recibe_401(cliente, demo) -> None:
    de_la_odontologa = _sesion_de(cliente, EMAIL_ODONTOLOGA)
    dueno_id = _alta(cliente, de_la_odontologa, EMAIL_DUENO, ["dueno"])
    del_dueno = _sesion_de(cliente, EMAIL_DUENO)
    assert _yo(cliente, del_dueno["access_token"]).status_code == 200

    assert _editar(cliente, de_la_odontologa, dueno_id, {"activo": False}).status_code == 200
    respuesta = _yo(cliente, del_dueno["access_token"])

    assert _es_el_401_de_sesion_invalida(respuesta)
    assert EMAIL_DUENO not in respuesta.text


def test_ses3g_restablecer_corta_todas_las_sesiones_y_el_login_nuevo_sirve(cliente, demo) -> None:
    de_la_odontologa = _sesion_de(cliente, EMAIL_ODONTOLOGA)
    sesion_a = _sesion_de(cliente, EMAIL_RECEPCIONISTA)
    sesion_b = _sesion_de(cliente, EMAIL_RECEPCIONISTA)
    assert _yo(cliente, sesion_a["access_token"]).status_code == 200

    restablecida = cliente.post(
        "/usuarios/2/restablecer-contrasena",
        json={"contrasena": "clave-nueva-2026"},
        headers=_bearer(de_la_odontologa["access_token"]),
    )
    cortadas = [_yo(cliente, s["access_token"]) for s in (sesion_a, sesion_b)]
    nueva = _sesion_de(cliente, EMAIL_RECEPCIONISTA, "clave-nueva-2026")
    con_la_nueva = _yo(cliente, nueva["access_token"])

    assert restablecida.status_code == 204
    assert all(_es_el_401_de_sesion_invalida(r) for r in cortadas)
    assert (con_la_nueva.status_code, con_la_nueva.json()["email"]) == (200, EMAIL_RECEPCIONISTA)


def test_ses3h_un_usuario_sin_roles_no_obtiene_su_usuario(cliente, demo, sesion) -> None:
    consultorio = sesion.get_one(ConsultorioModelo, demo.odontologa.consultorio_id)
    sin_roles = un_usuario(sesion, consultorio, contrasena=CONTRASENA, email=EMAIL_SIN_ROLES, roles=())
    de_sin_roles = _sesion_de(cliente, EMAIL_SIN_ROLES)  # V4: el login admite a un usuario activo sin roles

    respuesta = _yo(cliente, de_sin_roles["access_token"])

    assert respuesta.status_code == 403
    assert respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    assert respuesta.json()["codigos"] == ["RN-AU-05"]
    assert EMAIL_SIN_ROLES not in respuesta.text and "roles" not in respuesta.json()
    sesion.expire_all()
    assert sesion.get_one(UsuarioModelo, sin_roles.id).token_version == 0
