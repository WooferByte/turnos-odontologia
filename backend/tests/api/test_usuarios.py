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
from tests.factories import CONTRASENA_DE_PRUEBA, un_consultorio, un_profesional, un_usuario

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


def _roles_en_la_base(sesion: Session, usuario_id: int) -> set[str]:
    sesion.expire_all()
    return set(sesion.scalars(select(UsuarioRolModelo.rol).where(UsuarioRolModelo.usuario_id == usuario_id)))


def _token_version_en_la_base(sesion: Session, usuario_id: int) -> int:
    sesion.expire_all()
    return sesion.get_one(UsuarioModelo, usuario_id).token_version


def test_us093_ca1_la_odontologa_suma_el_rol_dueno_a_la_recepcionista(cliente, demo, sesion) -> None:
    de_la_recepcionista = _con_token_de(demo.recepcionista)
    assert cliente.get("/usuarios", headers=de_la_recepcionista).status_code == 403

    respuesta = cliente.patch(
        f"/usuarios/{demo.recepcionista.id}",
        json={"roles": ["recepcionista", "dueno"]},
        headers=_con_token_de(demo.odontologa),
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "id": demo.recepcionista.id,
        "email": EMAIL_RECEPCIONISTA,
        "roles": ["recepcionista", "dueno"],
        "activo": True,
    }
    assert _roles_en_la_base(sesion, demo.recepcionista.id) == {"recepcionista", "dueno"}
    assert _token_version_en_la_base(sesion, demo.recepcionista.id) == 0
    # Los roles se leen de la base en cada petición (RN-AU-02, D102): el mismo token ya vale.
    assert cliente.get("/usuarios", headers=de_la_recepcionista).status_code == 200


def test_us093_ca3_desactivar_a_la_recepcionista_corta_su_sesion(cliente, demo, sesion) -> None:
    login = cliente.post(
        "/auth/login", json={"email": EMAIL_RECEPCIONISTA, "contrasena": CONTRASENA_DE_PRUEBA}
    )
    assert login.status_code == 200
    access, refresh = login.json()["access_token"], login.json()["refresh_token"]
    assert cliente.get("/prestaciones", headers={"Authorization": f"Bearer {access}"}).status_code == 200

    respuesta = cliente.patch(
        f"/usuarios/{demo.recepcionista.id}", json={"activo": False}, headers=_con_token_de(demo.odontologa)
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["activo"] is False
    assert _token_version_en_la_base(sesion, demo.recepcionista.id) == 1
    con_access = cliente.get("/prestaciones", headers={"Authorization": f"Bearer {access}"})
    assert con_access.status_code == 401 and con_access.json()["codigos"] == ["RN-AU-03"]
    con_refresh = cliente.post("/auth/refresh", json={"refresh_token": refresh})
    assert con_refresh.status_code == 401 and con_refresh.json()["codigos"] == ["RN-AU-03"]
    nuevo_login = cliente.post(
        "/auth/login", json={"email": EMAIL_RECEPCIONISTA, "contrasena": CONTRASENA_DE_PRUEBA}
    )
    assert nuevo_login.status_code == 401
    en_la_lista = cliente.get("/usuarios", headers=_con_token_de(demo.odontologa)).json()
    assert [u["activo"] for u in en_la_lista if u["id"] == demo.recepcionista.id] == [False]


def _patch(cliente, usuario_id: int, cuerpo: dict, quien: UsuarioModelo):
    return cliente.patch(f"/usuarios/{usuario_id}", json=cuerpo, headers=_con_token_de(quien))


def test_us093_ca3_reactivar_no_revive_los_tokens_anteriores(cliente, demo, sesion) -> None:
    anterior = {"Authorization": f"Bearer {token_de(demo.recepcionista.id, token_version=0)}"}
    assert cliente.get("/prestaciones", headers=anterior).status_code == 200

    assert _patch(cliente, demo.recepcionista.id, {"activo": False}, demo.odontologa).status_code == 200
    reactivada = _patch(cliente, demo.recepcionista.id, {"activo": True}, demo.odontologa)

    assert reactivada.status_code == 200 and reactivada.json()["activo"] is True
    assert _token_version_en_la_base(sesion, demo.recepcionista.id) == 1
    assert cliente.get("/prestaciones", headers=anterior).status_code == 401
    nuevo = {"Authorization": f"Bearer {token_de(demo.recepcionista.id, token_version=1)}"}
    assert cliente.get("/prestaciones", headers=nuevo).status_code == 200


def test_us093_ca3_desactivar_a_quien_ya_esta_inactivo_no_cambia_nada(cliente, demo, sesion) -> None:
    respuesta = _patch(cliente, demo.administracion.id, {"activo": False}, demo.odontologa)

    assert respuesta.status_code == 200 and respuesta.json()["activo"] is False
    assert _token_version_en_la_base(sesion, demo.administracion.id) == 0


def test_us093_ca8_pasar_a_odontologo_a_otro_usuario_no_crea_un_profesional(cliente, demo, sesion) -> None:
    respuesta = _patch(cliente, demo.recepcionista.id, {"roles": ["odontologo"]}, demo.odontologa)

    assert respuesta.status_code == 200 and respuesta.json()["roles"] == ["odontologo"]
    assert [p.usuario_id for p in sesion.scalars(select(ProfesionalModelo))] == [demo.odontologa.id]


@pytest.mark.parametrize("usuario_id", ["recepcionista", "999"])
def test_us093_ca1_el_dueno_no_puede_cambiar_roles(cliente, demo, sesion, usuario_id) -> None:
    dueno = un_usuario(sesion, _consultorio_de(sesion, demo), roles=(Rol.DUENO,))
    destino = demo.recepcionista.id if usuario_id == "recepcionista" else int(usuario_id)

    respuesta = _patch(cliente, destino, {"roles": ["dueno"]}, dueno)

    assert respuesta.status_code == 403
    assert respuesta.json()["codigos"] == ["RN-AU-05"]
    assert _roles_en_la_base(sesion, demo.recepcionista.id) == {"recepcionista"}


def test_us093_ca1_un_usuario_inexistente_responde_404_rn_gl_04(cliente, demo) -> None:
    respuesta = _patch(cliente, 999, {"activo": False}, demo.odontologa)

    assert respuesta.status_code == 404
    assert respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-GL-04"]
    assert cuerpo["referencias"] == [{"recurso": "usuario", "recurso_id": 999, "motivo": "inexistente"}]


@pytest.mark.parametrize(
    ("cuerpo", "campo"),
    [
        ({"roles": []}, "roles"),
        ({"email": "otro@consultorio-demo.test"}, "email"),
        ({"contrasena": "otra-clave-2026"}, "contrasena"),
        ({"activo": None}, "activo"),
        ({"roles": None}, "roles"),
        ({"activo": "quizas"}, "activo"),
    ],
)
def test_us093_ca1_un_cuerpo_invalido_del_patch_responde_422_de_formato(
    cliente, demo, sesion, cuerpo, campo
) -> None:
    respuesta = _patch(cliente, demo.recepcionista.id, cuerpo, demo.odontologa)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []
    assert [e["campo"].split(".")[0] for e in respuesta.json()["errores"]] == [campo]
    assert _roles_en_la_base(sesion, demo.recepcionista.id) == {"recepcionista"}


def test_us093_ca1_la_entrada_se_evalua_antes_que_el_usuario_de_la_url(cliente, demo) -> None:
    respuesta = _patch(cliente, 999, {"roles": []}, demo.odontologa)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []


def test_us093_ca1_un_patch_vacio_no_cambia_nada(cliente, demo, sesion) -> None:
    respuesta = _patch(cliente, demo.recepcionista.id, {}, demo.odontologa)

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "id": demo.recepcionista.id,
        "email": EMAIL_RECEPCIONISTA,
        "roles": ["recepcionista"],
        "activo": True,
    }
    assert _token_version_en_la_base(sesion, demo.recepcionista.id) == 0
    assert _roles_en_la_base(sesion, demo.recepcionista.id) == {"recepcionista"}


def test_us093_ca1_se_cambian_los_roles_de_un_usuario_inactivo(cliente, demo, sesion) -> None:
    assert _patch(cliente, demo.recepcionista.id, {"activo": False}, demo.odontologa).status_code == 200

    respuesta = _patch(cliente, demo.recepcionista.id, {"roles": ["dueno"]}, demo.odontologa)

    assert respuesta.status_code == 200
    assert respuesta.json()["roles"] == ["dueno"] and respuesta.json()["activo"] is False
    assert _token_version_en_la_base(sesion, demo.recepcionista.id) == 1
    login = cliente.post(
        "/auth/login", json={"email": EMAIL_RECEPCIONISTA, "contrasena": CONTRASENA_DE_PRUEBA}
    )
    assert login.status_code == 401


DETALLE_DESACTIVARSE = "Nadie puede desactivarse a sí mismo."
DETALLE_SIN_ODONTOLOGO = "El consultorio no puede quedar sin un odontólogo activo."


def _un_colega(sesion: Session, demo: Escenario, **kw) -> UsuarioModelo:
    """Un segundo odontólogo ficticio (sin profesional vinculado, U16)."""
    return un_usuario(sesion, _consultorio_de(sesion, demo), roles=kw.pop("roles", (Rol.ODONTOLOGO,)), **kw)


def _es_rn_au_06(respuesta, detalle: str) -> None:
    assert respuesta.status_code == 409
    assert respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    assert respuesta.json()["codigos"] == ["RN-AU-06"]
    assert respuesta.json()["detail"] == detalle


def test_us093_ca5_la_odontologa_no_puede_desactivarse(cliente, demo, sesion) -> None:
    _un_colega(sesion, demo)

    respuesta = _patch(cliente, demo.odontologa.id, {"activo": False}, demo.odontologa)

    _es_rn_au_06(respuesta, DETALLE_DESACTIVARSE)
    assert _token_version_en_la_base(sesion, demo.odontologa.id) == 0
    assert sesion.get_one(UsuarioModelo, demo.odontologa.id).activo is True
    assert cliente.get("/usuarios", headers=_con_token_de(demo.odontologa)).status_code == 200


def test_us093_ca4_la_unica_odontologa_no_puede_quitarse_el_rol_odontologo(cliente, demo, sesion) -> None:
    respuesta = _patch(cliente, demo.odontologa.id, {"roles": ["dueno"]}, demo.odontologa)

    _es_rn_au_06(respuesta, DETALLE_SIN_ODONTOLOGO)
    assert _roles_en_la_base(sesion, demo.odontologa.id) == {"odontologo", "dueno"}


def test_us093_ca4_un_odontologo_inactivo_no_cuenta(cliente, demo, sesion) -> None:
    _un_colega(sesion, demo, activo=False)

    respuesta = _patch(cliente, demo.odontologa.id, {"roles": ["recepcionista"]}, demo.odontologa)

    _es_rn_au_06(respuesta, DETALLE_SIN_ODONTOLOGO)
    assert _roles_en_la_base(sesion, demo.odontologa.id) == {"odontologo", "dueno"}


def test_us093_ca4_con_otro_odontologo_activo_la_odontologa_deja_su_rol(cliente, demo, sesion) -> None:
    _un_colega(sesion, demo)

    respuesta = _patch(cliente, demo.odontologa.id, {"roles": ["dueno"]}, demo.odontologa)

    assert respuesta.status_code == 200 and respuesta.json()["roles"] == ["dueno"]
    assert _roles_en_la_base(sesion, demo.odontologa.id) == {"dueno"}
    # Ya sin el rol, el mismo token pierde el permiso de escribir usuarios (RN-AU-02).
    siguiente = cliente.post("/usuarios", json=_cuerpo_de_alta(), headers=_con_token_de(demo.odontologa))
    assert siguiente.status_code == 403 and siguiente.json()["codigos"] == ["RN-AU-05"]


def test_us093_ca5_el_permiso_y_la_entrada_se_evaluan_antes(cliente, demo, sesion) -> None:
    _un_colega(sesion, demo)

    sin_permiso = _patch(cliente, demo.odontologa.id, {"activo": False}, demo.recepcionista)
    mal_formado = _patch(cliente, demo.odontologa.id, {"activo": False, "roles": []}, demo.odontologa)

    assert sin_permiso.status_code == 403 and sin_permiso.json()["codigos"] == ["RN-AU-05"]
    assert mal_formado.status_code == 422 and mal_formado.json()["codigos"] == []
    assert sesion.get_one(UsuarioModelo, demo.odontologa.id).activo is True


def test_us093_ca5_roles_y_activo_en_el_mismo_pedido_no_cambian_nada_si_se_rechaza(
    cliente, demo, sesion
) -> None:
    respuesta = _patch(cliente, demo.odontologa.id, {"roles": ["dueno"], "activo": False}, demo.odontologa)

    _es_rn_au_06(respuesta, DETALLE_DESACTIVARSE)
    assert _roles_en_la_base(sesion, demo.odontologa.id) == {"odontologo", "dueno"}
    sesion.expire_all()
    assert sesion.get_one(UsuarioModelo, demo.odontologa.id).activo is True
    assert _token_version_en_la_base(sesion, demo.odontologa.id) == 0


def test_us093_ca4_roles_y_activo_de_otro_odontologo_en_el_mismo_pedido_se_aplican_juntos(
    cliente, demo, sesion
) -> None:
    colega = _un_colega(sesion, demo)

    respuesta = _patch(cliente, colega.id, {"roles": ["dueno"], "activo": False}, demo.odontologa)

    assert respuesta.status_code == 200
    assert respuesta.json()["roles"] == ["dueno"] and respuesta.json()["activo"] is False
    assert _token_version_en_la_base(sesion, colega.id) == 1
    assert _roles_en_la_base(sesion, colega.id) == {"dueno"}
    en_la_lista = {u["id"]: u for u in cliente.get("/usuarios", headers=_con_token_de(demo.odontologa)).json()}
    assert "odontologo" in en_la_lista[demo.odontologa.id]["roles"] and en_la_lista[demo.odontologa.id]["activo"]
