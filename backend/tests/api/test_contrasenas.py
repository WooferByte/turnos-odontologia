"""Restablecer y cambiar contraseñas por HTTP con ``TestClient`` sobre ``crear_app(engine)`` (US-093 CA-6, CA-7, CA-9).

Sin dobles: sesión, repositorios, hasher y firmador son los reales, con tokens reales (D211); solo el
reloj se sustituye. Las rondas de bcrypt son pocas para que la suite no se haga lenta. Todos los datos
y todas las contraseñas son ficticios (RN-PR-01).
"""
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_reloj
from app.domain.acceso.roles import Rol
from app.infrastructure.configuracion import ConfiguracionDeSesion
from app.infrastructure.db.modelos import ConsultorioModelo, UsuarioModelo
from app.main import crear_app
from tests.conftest import SECRETO_DE_PRUEBA, reloj_fijo
from tests.factories import un_consultorio, un_usuario

PROBLEMA_JSON = "application/problem+json"
ACTUAL = "demo-consultorio-2026"
NUEVA = "clave-nueva-2026"
OTRA = "otra-clave-2026"
EMAIL_ODONTOLOGA = "odontologa@consultorio-demo.test"
EMAIL_RECEPCIONISTA = "recepcion@consultorio-demo.test"
EMAIL_INACTIVO = "administracion@consultorio-demo.test"


@dataclass
class Escenario:
    odontologa: UsuarioModelo  # odontologo + dueno
    recepcionista: UsuarioModelo
    inactivo: UsuarioModelo  # solo dueno, inactivo, token_version 1


@pytest.fixture
def cliente(engine) -> TestClient:
    app = crear_app(engine, ConfiguracionDeSesion(SECRETO_DE_PRUEBA, rondas_bcrypt=4))
    app.dependency_overrides[get_reloj] = lambda: reloj_fijo
    return TestClient(app)


@pytest.fixture
def demo(sesion: Session) -> Escenario:
    consultorio = un_consultorio(sesion)
    odontologa = un_usuario(
        sesion, consultorio, contrasena=ACTUAL, email=EMAIL_ODONTOLOGA, roles=(Rol.ODONTOLOGO, Rol.DUENO)
    )
    recepcionista = un_usuario(
        sesion, consultorio, contrasena=ACTUAL, email=EMAIL_RECEPCIONISTA, roles=(Rol.RECEPCIONISTA,)
    )
    inactivo = un_usuario(
        sesion, consultorio, contrasena=ACTUAL, email=EMAIL_INACTIVO, activo=False, token_version=1,
        roles=(Rol.DUENO,),
    )
    return Escenario(odontologa, recepcionista, inactivo)


def _login(cliente: TestClient, email: str, contrasena: str):
    return cliente.post("/auth/login", json={"email": email, "contrasena": contrasena})


def _sesion_de(cliente: TestClient, usuario: UsuarioModelo, contrasena: str = ACTUAL) -> dict[str, str]:
    """Inicia sesión por la API y devuelve ``access_token`` y ``refresh_token``."""
    respuesta = _login(cliente, usuario.email, contrasena)
    assert respuesta.status_code == 200
    return respuesta.json()


def _bearer(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


def _en_la_base(sesion: Session, usuario: UsuarioModelo) -> UsuarioModelo:
    sesion.expire_all()
    return sesion.get_one(UsuarioModelo, usuario.id)


def _restablecer(cliente: TestClient, quien: dict[str, str], usuario_id: int, cuerpo: dict):
    return cliente.post(f"/usuarios/{usuario_id}/restablecer-contrasena", json=cuerpo, headers=_bearer(quien["access_token"]))


def _es_el_401_de_sesion_invalida(respuesta) -> bool:
    return (
        respuesta.status_code == 401
        and respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
        and respuesta.json()["codigos"] == ["RN-AU-03"]
    )


# --- US-093 CA-6: restablecer ------------------------------------------------------------------


def test_us093_ca6_la_odontologa_restablece_la_contrasena_de_la_recepcionista(cliente, demo, sesion) -> None:
    de_la_odontologa = _sesion_de(cliente, demo.odontologa)
    de_la_recepcionista = _sesion_de(cliente, demo.recepcionista)
    hash_anterior = _en_la_base(sesion, demo.recepcionista).hash_password

    respuesta = _restablecer(cliente, de_la_odontologa, demo.recepcionista.id, {"contrasena": NUEVA})

    assert respuesta.status_code == 204 and respuesta.content == b""
    guardado = _en_la_base(sesion, demo.recepcionista)
    assert guardado.hash_password != hash_anterior and guardado.hash_password.startswith("$2b$")
    assert NUEVA not in guardado.hash_password and guardado.token_version == 1
    assert _login(cliente, EMAIL_RECEPCIONISTA, NUEVA).status_code == 200
    vieja = _login(cliente, EMAIL_RECEPCIONISTA, ACTUAL)
    assert vieja.status_code == 401 and vieja.json()["codigos"] == ["RN-AU-04"]
    assert _es_el_401_de_sesion_invalida(
        cliente.get("/prestaciones", headers=_bearer(de_la_recepcionista["access_token"]))
    )
    refresh_viejo = cliente.post("/auth/refresh", json={"refresh_token": de_la_recepcionista["refresh_token"]})
    assert _es_el_401_de_sesion_invalida(refresh_viejo)
    assert cliente.get("/usuarios", headers=_bearer(de_la_odontologa["access_token"])).status_code == 200


def test_us093_ca6_la_recepcionista_y_el_dueno_no_pueden_restablecer(cliente, demo, sesion) -> None:
    dueno = un_usuario(sesion, sesion.get_one(ConsultorioModelo, demo.odontologa.consultorio_id), contrasena=ACTUAL,
                       roles=(Rol.DUENO,))
    de_la_recepcionista = _sesion_de(cliente, demo.recepcionista)
    del_dueno = _sesion_de(cliente, dueno)
    antes = {u.id: (u.hash_password, u.token_version) for u in (demo.odontologa, demo.recepcionista)}

    contra_la_odontologa = _restablecer(cliente, de_la_recepcionista, demo.odontologa.id, {"contrasena": NUEVA})
    contra_la_recepcionista = _restablecer(cliente, del_dueno, demo.recepcionista.id, {"contrasena": NUEVA})

    for respuesta in (contra_la_odontologa, contra_la_recepcionista):
        assert respuesta.status_code == 403 and respuesta.json()["codigos"] == ["RN-AU-05"]
    for usuario in (demo.odontologa, demo.recepcionista):
        guardado = _en_la_base(sesion, usuario)
        assert (guardado.hash_password, guardado.token_version) == antes[usuario.id]


def test_us093_ca9_una_contrasena_restablecida_de_9_caracteres_se_rechaza(cliente, demo, sesion) -> None:
    de_la_odontologa = _sesion_de(cliente, demo.odontologa)
    antes = _en_la_base(sesion, demo.recepcionista)
    hash_anterior = antes.hash_password

    respuesta = _restablecer(cliente, de_la_odontologa, demo.recepcionista.id, {"contrasena": "corta-123"})

    assert respuesta.status_code == 422 and respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-AU-07"]
    assert [(e["campo"], e["codigo"]) for e in cuerpo["errores"]] == [("contrasena", "RN-AU-07")]
    assert "corta-123" not in respuesta.text
    guardado = _en_la_base(sesion, demo.recepcionista)
    assert (guardado.hash_password, guardado.token_version) == (hash_anterior, 0)
    assert _login(cliente, EMAIL_RECEPCIONISTA, ACTUAL).status_code == 200


def test_us093_ca6_restablecer_a_un_usuario_inactivo_no_lo_reactiva(cliente, demo, sesion) -> None:
    de_la_odontologa = _sesion_de(cliente, demo.odontologa)

    respuesta = _restablecer(cliente, de_la_odontologa, demo.inactivo.id, {"contrasena": NUEVA})

    assert respuesta.status_code == 204
    guardado = _en_la_base(sesion, demo.inactivo)
    assert guardado.activo is False and guardado.token_version == 2
    inactivo = _login(cliente, EMAIL_INACTIVO, NUEVA)
    assert inactivo.status_code == 401 and inactivo.json()["codigos"] == ["RN-AU-04"]
    reactivado = cliente.patch(
        f"/usuarios/{demo.inactivo.id}", json={"activo": True}, headers=_bearer(de_la_odontologa["access_token"])
    )
    assert reactivado.status_code == 200
    assert _login(cliente, EMAIL_INACTIVO, NUEVA).status_code == 200
    assert _login(cliente, EMAIL_INACTIVO, ACTUAL).status_code == 401


def test_us093_ca6_la_propia_contrasena_no_se_restablece(cliente, demo, sesion) -> None:
    de_la_odontologa = _sesion_de(cliente, demo.odontologa)
    hash_anterior = _en_la_base(sesion, demo.odontologa).hash_password

    respuesta = _restablecer(cliente, de_la_odontologa, demo.odontologa.id, {"contrasena": NUEVA})

    assert respuesta.status_code == 409 and respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-AU-10"]
    assert cuerpo["detail"] == "La propia contraseña se cambia con POST /auth/cambiar-contrasena, pidiendo la actual."
    guardado = _en_la_base(sesion, demo.odontologa)
    assert (guardado.hash_password, guardado.token_version) == (hash_anterior, 0)
    assert cliente.get("/usuarios", headers=_bearer(de_la_odontologa["access_token"])).status_code == 200


def test_us093_ca6_el_usuario_de_la_url_se_evalua_despues_del_permiso_y_de_la_entrada(cliente, demo, sesion) -> None:
    dueno = un_usuario(sesion, sesion.get_one(ConsultorioModelo, demo.odontologa.consultorio_id), contrasena=ACTUAL,
                       roles=(Rol.DUENO,))
    de_la_odontologa = _sesion_de(cliente, demo.odontologa)
    del_dueno = _sesion_de(cliente, dueno)

    inexistente = _restablecer(cliente, de_la_odontologa, 999, {"contrasena": NUEVA})
    sin_permiso = _restablecer(cliente, del_dueno, 999, {"contrasena": NUEVA})
    sin_cuerpo = _restablecer(cliente, de_la_odontologa, 999, {})

    assert inexistente.status_code == 404 and inexistente.json()["codigos"] == ["RN-GL-04"]
    assert sin_permiso.status_code == 403 and sin_permiso.json()["codigos"] == ["RN-AU-05"]
    assert sin_cuerpo.status_code == 422 and sin_cuerpo.json()["codigos"] == []
    assert [e["campo"] for e in sin_cuerpo.json()["errores"]] == ["contrasena"]


def test_us093_ca6_sin_sesion_se_responde_401_antes_que_la_entrada(cliente, demo, sesion) -> None:
    hash_anterior = _en_la_base(sesion, demo.recepcionista).hash_password

    respuesta = cliente.post(f"/usuarios/{demo.recepcionista.id}/restablecer-contrasena", json={})

    assert _es_el_401_de_sesion_invalida(respuesta)
    assert _en_la_base(sesion, demo.recepcionista).hash_password == hash_anterior


@pytest.mark.parametrize(
    "cuerpo",
    [{}, {"contrasena": 1234567890}, {"contrasena": None}, {"contrasena": NUEVA, "token_version": 0}],
    ids=["vacio", "no_es_texto", "nulo", "campo_de_mas"],
)
def test_us093_ca6_un_cuerpo_mal_formado_se_rechaza_todo_junto(cliente, demo, sesion, cuerpo) -> None:
    de_la_odontologa = _sesion_de(cliente, demo.odontologa)
    hash_anterior = _en_la_base(sesion, demo.recepcionista).hash_password

    respuesta = _restablecer(cliente, de_la_odontologa, demo.recepcionista.id, cuerpo)

    assert respuesta.status_code == 422 and respuesta.json()["codigos"] == []
    assert respuesta.json()["errores"]
    guardado = _en_la_base(sesion, demo.recepcionista)
    assert (guardado.hash_password, guardado.token_version) == (hash_anterior, 0)


CONTRASENAS_LIMITE = {
    "10 caracteres": "abcdefghij",
    "72 bytes": "á" * 34 + "abcd",  # 34 * 2 + 4 = 72 bytes, 38 caracteres
    "espacios en los extremos": "  clave-con-espacios  ",
}
CONTRASENA_DE_73_BYTES = "á" * 36 + "a"  # 37 caracteres, 73 bytes


@pytest.mark.parametrize("nombre", list(CONTRASENAS_LIMITE))
def test_us093_ca9_10_caracteres_y_72_bytes_se_aceptan_al_restablecer(cliente, demo, nombre) -> None:
    contrasena = CONTRASENAS_LIMITE[nombre]
    assert len(contrasena) >= 10 and len(contrasena.encode("utf-8")) <= 72
    de_la_odontologa = _sesion_de(cliente, demo.odontologa)

    respuesta = _restablecer(cliente, de_la_odontologa, demo.recepcionista.id, {"contrasena": contrasena})

    assert respuesta.status_code == 204
    assert _login(cliente, EMAIL_RECEPCIONISTA, contrasena).status_code == 200
    if contrasena != contrasena.strip():
        assert _login(cliente, EMAIL_RECEPCIONISTA, contrasena.strip()).status_code == 401


def test_us093_ca9_73_bytes_no_se_aceptan_al_restablecer(cliente, demo, sesion) -> None:
    assert len(CONTRASENA_DE_73_BYTES) == 37 and len(CONTRASENA_DE_73_BYTES.encode("utf-8")) == 73
    de_la_odontologa = _sesion_de(cliente, demo.odontologa)

    respuesta = _restablecer(cliente, de_la_odontologa, demo.recepcionista.id, {"contrasena": CONTRASENA_DE_73_BYTES})

    assert respuesta.status_code == 422 and respuesta.json()["codigos"] == ["RN-AU-07"]
    assert _en_la_base(sesion, demo.recepcionista).token_version == 0


def test_us093_ca9_el_largo_se_informa_antes_que_la_propia_al_restablecer(cliente, demo, sesion) -> None:
    de_la_odontologa = _sesion_de(cliente, demo.odontologa)

    respuesta = _restablecer(cliente, de_la_odontologa, demo.odontologa.id, {"contrasena": "corta-123"})

    assert respuesta.status_code == 422 and respuesta.json()["codigos"] == ["RN-AU-07"]
    assert _en_la_base(sesion, demo.odontologa).token_version == 0


def test_us093_ca9_el_formato_se_informa_antes_que_el_largo_al_restablecer(cliente, demo, sesion) -> None:
    de_la_odontologa = _sesion_de(cliente, demo.odontologa)

    respuesta = _restablecer(
        cliente, de_la_odontologa, demo.recepcionista.id, {"contrasena": "corta-123", "activo": True}
    )

    assert respuesta.status_code == 422 and respuesta.json()["codigos"] == []
    assert [e["campo"] for e in respuesta.json()["errores"]] == ["activo"]
    assert all(e["codigo"] is None for e in respuesta.json()["errores"])
    assert _en_la_base(sesion, demo.recepcionista).token_version == 0


# --- US-093 CA-7: cambiar la propia -------------------------------------------------------------


def _cambiar(cliente: TestClient, quien: dict[str, str], cuerpo: dict):
    return cliente.post("/auth/cambiar-contrasena", json=cuerpo, headers=_bearer(quien["access_token"]))


def _cuerpo_de_cambio(**cambios) -> dict:
    return {"contrasena_actual": ACTUAL, "contrasena_nueva": NUEVA, **cambios}


def test_us093_ca7_la_recepcionista_cambia_la_suya_y_sus_otras_sesiones_caen(cliente, demo, sesion) -> None:
    sesion_a = _sesion_de(cliente, demo.recepcionista)
    sesion_b = _sesion_de(cliente, demo.recepcionista)
    hash_anterior = _en_la_base(sesion, demo.recepcionista).hash_password

    respuesta = _cambiar(cliente, sesion_a, _cuerpo_de_cambio())

    assert respuesta.status_code == 200
    assert respuesta.headers["cache-control"] == "no-store"
    tokens = respuesta.json()
    assert set(tokens) == {"access_token", "refresh_token", "token_type", "expires_in"}
    assert tokens["token_type"] == "bearer" and tokens["expires_in"] > 0
    guardado = _en_la_base(sesion, demo.recepcionista)
    assert guardado.token_version == 1 and guardado.hash_password != hash_anterior
    assert guardado.hash_password.startswith("$2b$") and NUEVA not in guardado.hash_password
    assert cliente.get("/prestaciones", headers=_bearer(tokens["access_token"])).status_code == 200
    assert cliente.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 200
    assert _es_el_401_de_sesion_invalida(cliente.get("/prestaciones", headers=_bearer(sesion_b["access_token"])))
    assert _es_el_401_de_sesion_invalida(
        cliente.post("/auth/refresh", json={"refresh_token": sesion_b["refresh_token"]})
    )
    assert _es_el_401_de_sesion_invalida(cliente.get("/prestaciones", headers=_bearer(sesion_a["access_token"])))
    assert _login(cliente, EMAIL_RECEPCIONISTA, NUEVA).status_code == 200
    vieja = _login(cliente, EMAIL_RECEPCIONISTA, ACTUAL)
    assert vieja.status_code == 401 and vieja.json()["codigos"] == ["RN-AU-04"]


def test_us093_ca7_con_la_contrasena_actual_incorrecta_no_cambia_nada(cliente, demo, sesion) -> None:
    de_la_recepcionista = _sesion_de(cliente, demo.recepcionista)
    hash_anterior = _en_la_base(sesion, demo.recepcionista).hash_password

    respuesta = _cambiar(cliente, de_la_recepcionista, _cuerpo_de_cambio(contrasena_actual="no-es-la-actual-2026"))

    assert respuesta.status_code == 422 and respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-AU-09"]
    assert cuerpo["detail"] == "La contraseña actual no es correcta."
    assert "no-es-la-actual-2026" not in respuesta.text and NUEVA not in respuesta.text
    assert cliente.get("/prestaciones", headers=_bearer(de_la_recepcionista["access_token"])).status_code == 200
    guardado = _en_la_base(sesion, demo.recepcionista)
    assert (guardado.hash_password, guardado.token_version) == (hash_anterior, 0)


def test_us093_ca9_una_contrasena_nueva_de_9_caracteres_se_rechaza(cliente, demo, sesion) -> None:
    de_la_recepcionista = _sesion_de(cliente, demo.recepcionista)
    hash_anterior = _en_la_base(sesion, demo.recepcionista).hash_password

    respuesta = _cambiar(cliente, de_la_recepcionista, _cuerpo_de_cambio(contrasena_nueva="corta-123"))

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-AU-07"]
    assert [(e["campo"], e["codigo"]) for e in cuerpo["errores"]] == [("contrasena_nueva", "RN-AU-07")]
    assert "corta-123" not in respuesta.text
    assert cliente.get("/prestaciones", headers=_bearer(de_la_recepcionista["access_token"])).status_code == 200
    guardado = _en_la_base(sesion, demo.recepcionista)
    assert (guardado.hash_password, guardado.token_version) == (hash_anterior, 0)


def test_us093_ca7_el_odontologo_y_el_dueno_tambien_cambian_la_suya_y_un_usuario_sin_roles_no(
    cliente, demo, sesion
) -> None:
    consultorio = sesion.get_one(ConsultorioModelo, demo.odontologa.consultorio_id)
    dueno = un_usuario(sesion, consultorio, contrasena=ACTUAL, roles=(Rol.DUENO,))
    sin_roles = un_usuario(sesion, consultorio, contrasena=ACTUAL)

    for usuario in (demo.odontologa, dueno):
        respuesta = _cambiar(cliente, _sesion_de(cliente, usuario), _cuerpo_de_cambio())
        assert respuesta.status_code == 200
        assert _en_la_base(sesion, usuario).token_version == 1
    hash_anterior = _en_la_base(sesion, sin_roles).hash_password

    rechazada = _cambiar(cliente, _sesion_de(cliente, sin_roles), _cuerpo_de_cambio())

    assert rechazada.status_code == 403 and rechazada.json()["codigos"] == ["RN-AU-05"]
    guardado = _en_la_base(sesion, sin_roles)
    assert (guardado.hash_password, guardado.token_version) == (hash_anterior, 0)


def test_us093_ca7_una_contrasena_actual_de_mas_de_72_bytes_cuenta_como_incorrecta(cliente, demo, sesion) -> None:
    de_la_recepcionista = _sesion_de(cliente, demo.recepcionista)
    de_73_bytes = "á" * 36 + "a"
    assert len(de_73_bytes.encode("utf-8")) == 73

    respuesta = _cambiar(cliente, de_la_recepcionista, _cuerpo_de_cambio(contrasena_actual=de_73_bytes))

    assert respuesta.status_code == 422 and respuesta.json()["codigos"] == ["RN-AU-09"]
    assert _en_la_base(sesion, demo.recepcionista).token_version == 0


def test_us093_ca7_la_nueva_igual_a_la_actual_se_acepta(cliente, demo, sesion) -> None:
    de_la_recepcionista = _sesion_de(cliente, demo.recepcionista)

    respuesta = _cambiar(cliente, de_la_recepcionista, _cuerpo_de_cambio(contrasena_nueva=ACTUAL))

    assert respuesta.status_code == 200 and "access_token" in respuesta.json()
    assert _en_la_base(sesion, demo.recepcionista).token_version == 1
    assert _login(cliente, EMAIL_RECEPCIONISTA, ACTUAL).status_code == 200


def test_us093_ca7_sin_sesion_o_con_una_sesion_que_ya_no_vale_se_responde_401(cliente, demo, sesion) -> None:
    de_la_odontologa = _sesion_de(cliente, demo.odontologa)
    de_la_recepcionista = _sesion_de(cliente, demo.recepcionista)
    assert _restablecer(cliente, de_la_odontologa, demo.recepcionista.id, {"contrasena": NUEVA}).status_code == 204
    hash_anterior = _en_la_base(sesion, demo.recepcionista).hash_password

    sin_cabecera = cliente.post("/auth/cambiar-contrasena", json={})
    con_access_anterior = _cambiar(cliente, de_la_recepcionista, _cuerpo_de_cambio(contrasena_actual=NUEVA))

    assert _es_el_401_de_sesion_invalida(sin_cabecera)
    assert _es_el_401_de_sesion_invalida(con_access_anterior)
    guardado = _en_la_base(sesion, demo.recepcionista)
    assert (guardado.hash_password, guardado.token_version) == (hash_anterior, 1)


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"contrasena_nueva": NUEVA},
        {"contrasena_actual": "", "contrasena_nueva": NUEVA},
        {"contrasena_actual": ACTUAL},
        {"contrasena_actual": ACTUAL, "contrasena_nueva": NUEVA, "email": EMAIL_RECEPCIONISTA},
    ],
    ids=["sin_actual", "actual_vacia", "sin_nueva", "campo_de_mas"],
)
def test_us093_ca7_un_cuerpo_mal_formado_se_rechaza_todo_junto(cliente, demo, sesion, cuerpo) -> None:
    de_la_recepcionista = _sesion_de(cliente, demo.recepcionista)
    hash_anterior = _en_la_base(sesion, demo.recepcionista).hash_password

    respuesta = _cambiar(cliente, de_la_recepcionista, cuerpo)

    assert respuesta.status_code == 422 and respuesta.json()["codigos"] == []
    assert respuesta.json()["errores"]
    guardado = _en_la_base(sesion, demo.recepcionista)
    assert (guardado.hash_password, guardado.token_version) == (hash_anterior, 0)


def test_us093_ca7_sin_ninguno_de_los_dos_campos_se_informan_los_dos_errores_juntos(cliente, demo) -> None:
    de_la_recepcionista = _sesion_de(cliente, demo.recepcionista)

    respuesta = _cambiar(cliente, de_la_recepcionista, {})

    assert respuesta.status_code == 422
    assert sorted(e["campo"] for e in respuesta.json()["errores"]) == ["contrasena_actual", "contrasena_nueva"]


@pytest.mark.parametrize("nombre", list(CONTRASENAS_LIMITE))
def test_us093_ca9_10_caracteres_y_72_bytes_se_aceptan_al_cambiar(cliente, demo, nombre) -> None:
    contrasena = CONTRASENAS_LIMITE[nombre]
    de_la_recepcionista = _sesion_de(cliente, demo.recepcionista)

    respuesta = _cambiar(cliente, de_la_recepcionista, _cuerpo_de_cambio(contrasena_nueva=contrasena))

    assert respuesta.status_code == 200
    assert _login(cliente, EMAIL_RECEPCIONISTA, contrasena).status_code == 200
    if contrasena != contrasena.strip():
        assert _login(cliente, EMAIL_RECEPCIONISTA, contrasena.strip()).status_code == 401


def test_us093_ca9_73_bytes_no_se_aceptan_al_cambiar(cliente, demo, sesion) -> None:
    de_la_recepcionista = _sesion_de(cliente, demo.recepcionista)

    respuesta = _cambiar(cliente, de_la_recepcionista, _cuerpo_de_cambio(contrasena_nueva=CONTRASENA_DE_73_BYTES))

    assert respuesta.status_code == 422 and respuesta.json()["codigos"] == ["RN-AU-07"]
    assert _en_la_base(sesion, demo.recepcionista).token_version == 0


def test_us093_ca9_el_largo_se_informa_antes_que_la_actual_incorrecta(cliente, demo, sesion) -> None:
    de_la_recepcionista = _sesion_de(cliente, demo.recepcionista)

    respuesta = _cambiar(
        cliente, de_la_recepcionista, _cuerpo_de_cambio(contrasena_actual="no-es-la-actual-2026", contrasena_nueva="corta-123")
    )

    assert respuesta.status_code == 422 and respuesta.json()["codigos"] == ["RN-AU-07"]
    assert _en_la_base(sesion, demo.recepcionista).token_version == 0


def test_us093_ca9_el_formato_se_informa_antes_que_el_largo_al_cambiar(cliente, demo, sesion) -> None:
    de_la_recepcionista = _sesion_de(cliente, demo.recepcionista)

    respuesta = _cambiar(
        cliente, de_la_recepcionista, _cuerpo_de_cambio(contrasena_nueva="corta-123", email=EMAIL_RECEPCIONISTA)
    )

    assert respuesta.status_code == 422 and respuesta.json()["codigos"] == []
    assert [e["campo"] for e in respuesta.json()["errores"]] == ["email"]
    assert _en_la_base(sesion, demo.recepcionista).token_version == 0
