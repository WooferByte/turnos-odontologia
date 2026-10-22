"""``/usuarios`` por HTTP con ``TestClient`` sobre ``crear_app(engine)`` (US-093 CA-1 a CA-5, CA-8, CA-9).

Sin dobles: sesión, repositorios, hasher y firmador son los reales, con tokens reales (D211); solo
el reloj se sustituye. Las rondas de bcrypt son pocas para que las altas no hagan lenta la suite.
"""
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_reloj
from app.domain.acceso.roles import Rol
from app.infrastructure.configuracion import ConfiguracionDeSesion
from app.infrastructure.db.modelos import ConsultorioModelo, ProfesionalModelo, UsuarioModelo, UsuarioRolModelo
from app.main import crear_app
from tests.conftest import SECRETO_DE_PRUEBA, reloj_fijo, token_de
from tests.factories import un_consultorio, un_profesional, un_usuario

PROBLEMA_JSON = "application/problem+json"
CONTRASENA_VALIDA = "clave-ficticia-2026"
EMAIL_ODONTOLOGA = "odontologa@consultorio-demo.test"
EMAIL_RECEPCIONISTA = "recepcion@consultorio-demo.test"
EMAIL_INACTIVO = "administracion@consultorio-demo.test"
CAMPOS_DE_USUARIO_SALIDA = {"id", "email", "roles", "activo"}


@dataclass
class Escenario:
    odontologa: UsuarioModelo
    recepcionista: UsuarioModelo
    administracion: UsuarioModelo  # inactivo, solo dueno


@pytest.fixture
def cliente(engine) -> TestClient:
    app = crear_app(engine, ConfiguracionDeSesion(SECRETO_DE_PRUEBA, rondas_bcrypt=4))
    app.dependency_overrides[get_reloj] = lambda: reloj_fijo
    return TestClient(app)


@pytest.fixture
def demo(sesion: Session) -> Escenario:
    """La odontóloga y la recepcionista de la demo y un tercer usuario inactivo con el rol ``dueno``."""
    consultorio = un_consultorio(sesion)
    odontologa = un_usuario(
        sesion, consultorio, email=EMAIL_ODONTOLOGA, roles=(Rol.ODONTOLOGO, Rol.DUENO)
    )
    un_profesional(sesion, consultorio, usuario_id=odontologa.id)
    recepcionista = un_usuario(sesion, consultorio, email=EMAIL_RECEPCIONISTA, roles=(Rol.RECEPCIONISTA,))
    administracion = un_usuario(
        sesion, consultorio, email=EMAIL_INACTIVO, activo=False, roles=(Rol.DUENO,)
    )
    return Escenario(odontologa, recepcionista, administracion)


def _con_token_de(usuario: UsuarioModelo) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_de(usuario.id, token_version=usuario.token_version)}"}


def _cuerpo_de_alta(**cambios) -> dict:
    return {
        "email": "turnos@consultorio-demo.test",
        "contrasena": CONTRASENA_VALIDA,
        "roles": ["recepcionista"],
        **cambios,
    }


def _usuarios_en_la_base(sesion: Session) -> list[UsuarioModelo]:
    sesion.expire_all()
    return list(sesion.scalars(select(UsuarioModelo).order_by(UsuarioModelo.id)))


def test_us093_ca1_la_odontologa_lista_los_usuarios_con_sus_roles(cliente, demo) -> None:
    respuesta = cliente.get("/usuarios", headers=_con_token_de(demo.odontologa))

    assert respuesta.status_code == 200
    usuarios = respuesta.json()
    assert [u["id"] for u in usuarios] == [demo.odontologa.id, demo.recepcionista.id, demo.administracion.id]
    assert usuarios[0] == {
        "id": demo.odontologa.id,
        "email": EMAIL_ODONTOLOGA,
        "roles": ["odontologo", "dueno"],
        "activo": True,
    }
    assert usuarios[1]["roles"] == ["recepcionista"] and usuarios[1]["activo"] is True
    assert usuarios[2]["roles"] == ["dueno"] and usuarios[2]["activo"] is False


def test_us093_ca1_la_odontologa_crea_una_recepcionista_que_inicia_sesion(cliente, demo, sesion) -> None:
    respuesta = cliente.post("/usuarios", json=_cuerpo_de_alta(), headers=_con_token_de(demo.odontologa))

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert set(cuerpo) == CAMPOS_DE_USUARIO_SALIDA
    assert cuerpo == {
        "id": cuerpo["id"],
        "email": "turnos@consultorio-demo.test",
        "roles": ["recepcionista"],
        "activo": True,
    }
    creado = _usuarios_en_la_base(sesion)[-1]
    assert creado.id == cuerpo["id"]
    assert creado.hash_password.startswith("$2b$") and CONTRASENA_VALIDA not in creado.hash_password
    assert creado.token_version == 0
    login = cliente.post(
        "/auth/login", json={"email": "turnos@consultorio-demo.test", "contrasena": CONTRASENA_VALIDA}
    )
    assert login.status_code == 200
    cabecera = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert cliente.post("/turnos", json={}, headers=cabecera).status_code != 403


def test_us093_ca9_contrasena_inicial_de_9_caracteres_responde_422_rn_au_07(cliente, demo, sesion) -> None:
    respuesta = cliente.post(
        "/usuarios", json=_cuerpo_de_alta(contrasena="corta-123"), headers=_con_token_de(demo.odontologa)
    )

    assert respuesta.status_code == 422
    assert respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-AU-07"]
    assert [(e["campo"], e["codigo"]) for e in cuerpo["errores"]] == [("contrasena", "RN-AU-07")]
    assert "corta-123" not in respuesta.text
    assert len(_usuarios_en_la_base(sesion)) == 3


def test_us093_ca2_email_repetido_con_otras_mayusculas_responde_409_rn_au_08(cliente, demo, sesion) -> None:
    respuesta = cliente.post(
        "/usuarios",
        json=_cuerpo_de_alta(email=" RECEPCION@consultorio-demo.test"),
        headers=_con_token_de(demo.odontologa),
    )

    assert respuesta.status_code == 409
    assert respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    assert respuesta.json()["codigos"] == ["RN-AU-08"]
    assert [u.email for u in _usuarios_en_la_base(sesion)].count(EMAIL_RECEPCIONISTA) == 1
    assert len(_usuarios_en_la_base(sesion)) == 3


def _consultorio_de(sesion: Session, demo: Escenario) -> ConsultorioModelo:
    return sesion.get_one(ConsultorioModelo, demo.odontologa.consultorio_id)


def test_us093_ca1_la_lista_no_expone_la_contrasena_ni_la_version_del_token(cliente, demo) -> None:
    respuesta = cliente.get("/usuarios", headers=_con_token_de(demo.odontologa))

    assert len(respuesta.json()) == 3
    assert all(set(usuario) == CAMPOS_DE_USUARIO_SALIDA for usuario in respuesta.json())
    assert "hash_password" not in respuesta.text and "token_version" not in respuesta.text


def test_us093_ca1_el_dueno_lee_pero_la_recepcionista_no(cliente, demo, sesion) -> None:
    dueno = un_usuario(sesion, _consultorio_de(sesion, demo), roles=(Rol.DUENO,))

    del_dueno = cliente.get("/usuarios", headers=_con_token_de(dueno))
    de_la_recepcionista = cliente.get("/usuarios", headers=_con_token_de(demo.recepcionista))

    assert del_dueno.status_code == 200 and len(del_dueno.json()) == 4
    assert de_la_recepcionista.status_code == 403
    assert de_la_recepcionista.json()["codigos"] == ["RN-AU-05"]


def test_us093_ca1_la_recepcionista_y_el_dueno_no_pueden_crear_usuarios(cliente, demo, sesion) -> None:
    dueno = un_usuario(sesion, _consultorio_de(sesion, demo), roles=(Rol.DUENO,))

    for quien in (demo.recepcionista, dueno):
        respuesta = cliente.post("/usuarios", json=_cuerpo_de_alta(), headers=_con_token_de(quien))

        assert respuesta.status_code == 403
        assert respuesta.json()["codigos"] == ["RN-AU-05"]
    assert len(_usuarios_en_la_base(sesion)) == 4


def test_us093_ca1_el_email_se_guarda_normalizado(cliente, demo, sesion) -> None:
    respuesta = cliente.post(
        "/usuarios",
        json=_cuerpo_de_alta(email="  Turnos@Consultorio-Demo.TEST "),
        headers=_con_token_de(demo.odontologa),
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["email"] == "turnos@consultorio-demo.test"
    assert _usuarios_en_la_base(sesion)[-1].email == "turnos@consultorio-demo.test"
    login = cliente.post(
        "/auth/login", json={"email": "turnos@consultorio-demo.test", "contrasena": CONTRASENA_VALIDA}
    )
    assert login.status_code == 200


EMAIL_DE_255 = "a" * (255 - len("@consultorio-demo.test")) + "@consultorio-demo.test"
EMAIL_DE_254 = "a" * (254 - len("@consultorio-demo.test")) + "@consultorio-demo.test"


@pytest.mark.parametrize(
    ("cambios", "campo"),
    [
        ({"roles": []}, "roles"),
        ({"roles": ["administrador"]}, "roles"),
        ({"roles": ["recepcionista", "recepcionista"]}, "roles"),
        ({"email": "sin-arroba"}, "email"),
        ({"email": "a@"}, "email"),
        ({"email": "@b"}, "email"),
        ({"email": "a b@c.test"}, "email"),
        ({"email": EMAIL_DE_255}, "email"),
        ({"activo": True}, "activo"),
    ],
)
def test_us093_ca1_un_cuerpo_mal_formado_se_rechaza_con_un_422_de_formato(
    cliente, demo, sesion, cambios, campo
) -> None:
    respuesta = cliente.post(
        "/usuarios", json=_cuerpo_de_alta(**cambios), headers=_con_token_de(demo.odontologa)
    )

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == []
    assert [e["campo"].split(".")[0] for e in cuerpo["errores"]] == [campo]
    assert len(_usuarios_en_la_base(sesion)) == 3


def test_us093_ca1_un_email_valido_de_254_caracteres_se_acepta(cliente, demo) -> None:
    respuesta = cliente.post(
        "/usuarios", json=_cuerpo_de_alta(email=EMAIL_DE_254), headers=_con_token_de(demo.odontologa)
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["email"] == EMAIL_DE_254


def test_us093_ca1_un_cuerpo_con_email_y_roles_invalidos_informa_los_dos_errores_juntos(cliente, demo) -> None:
    respuesta = cliente.post(
        "/usuarios",
        json=_cuerpo_de_alta(email="sin-arroba", roles=[]),
        headers=_con_token_de(demo.odontologa),
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []
    assert sorted(e["campo"] for e in respuesta.json()["errores"]) == ["email", "roles"]


def test_us093_ca1_sin_sesion_se_responde_401_antes_que_la_entrada(cliente, demo, sesion) -> None:
    respuesta = cliente.post("/usuarios", json=_cuerpo_de_alta(roles=[]))

    assert respuesta.status_code == 401
    assert respuesta.json()["codigos"] == ["RN-AU-03"]
    assert len(_usuarios_en_la_base(sesion)) == 3


def test_us093_ca9_10_caracteres_y_72_bytes_se_aceptan_73_bytes_no(cliente, demo, sesion) -> None:
    cabecera = _con_token_de(demo.odontologa)
    de_10 = "a" * 10
    de_72_bytes = "á" * 36
    de_73_bytes = "á" * 36 + "a"
    assert len(de_73_bytes) == 37 and len(de_73_bytes.encode("utf-8")) == 73

    respuestas = [
        cliente.post(
            "/usuarios",
            json=_cuerpo_de_alta(email=f"u{i}@consultorio-demo.test", contrasena=contrasena),
            headers=cabecera,
        )
        for i, contrasena in enumerate((de_10, de_72_bytes, de_73_bytes))
    ]

    assert [r.status_code for r in respuestas] == [201, 201, 422]
    assert respuestas[2].json()["codigos"] == ["RN-AU-07"]
    assert len(_usuarios_en_la_base(sesion)) == 5


def test_us093_ca9_el_formato_se_informa_antes_que_el_largo_de_la_contrasena(cliente, demo, sesion) -> None:
    respuesta = cliente.post(
        "/usuarios",
        json=_cuerpo_de_alta(email="sin-arroba", contrasena="corta-123"),
        headers=_con_token_de(demo.odontologa),
    )

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == []
    assert [e["campo"] for e in cuerpo["errores"]] == ["email"]
    assert "RN-AU-07" not in respuesta.text
    assert len(_usuarios_en_la_base(sesion)) == 3


def test_us093_ca2_el_email_de_un_usuario_inactivo_sigue_ocupado(cliente, demo) -> None:
    respuesta = cliente.post(
        "/usuarios", json=_cuerpo_de_alta(email=EMAIL_INACTIVO), headers=_con_token_de(demo.odontologa)
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["codigos"] == ["RN-AU-08"]


def test_us093_ca2_con_email_repetido_y_contrasena_corta_se_informa_la_entrada(cliente, demo) -> None:
    respuesta = cliente.post(
        "/usuarios",
        json=_cuerpo_de_alta(email=EMAIL_RECEPCIONISTA, contrasena="corta-123"),
        headers=_con_token_de(demo.odontologa),
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == ["RN-AU-07"]


def test_us093_ca8_asignar_odontologo_no_crea_un_profesional(cliente, demo, sesion) -> None:
    respuesta = cliente.post(
        "/usuarios",
        json=_cuerpo_de_alta(email="colega@consultorio-demo.test", roles=["odontologo"]),
        headers=_con_token_de(demo.odontologa),
    )

    assert respuesta.status_code == 201
    profesionales = list(sesion.scalars(select(ProfesionalModelo)))
    assert [p.usuario_id for p in profesionales] == [demo.odontologa.id]
