"""Protección del panel por HTTP: token real, usuario y roles de la base, sin dobles de la autenticación.

US-092 CA-1 a CA-4, US-091 CA-1 y CA-3; RN-AU-01 a RN-AU-05 (design R9 a R12, R17). Solo se
sustituye el reloj (``get_reloj``); el token, el usuario y los roles son los reales.
"""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.api.deps import get_reloj
from app.domain.acceso.roles import Rol
from app.domain.acceso.sesion import TipoDeToken
from app.domain.tiempo import UTC
from app.infrastructure.configuracion import ConfiguracionDeSesion
from app.infrastructure.db.modelos import PrestacionModelo, TurnoModelo
from app.main import crear_app
from tests.conftest import RELOJ_FIJO, SECRETO_DE_PRUEBA, token_de
from app.infrastructure.repositories.usuarios import RepositorioUsuariosSqlAlchemy
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
    un_usuario,
)

PROBLEMA_JSON = "application/problem+json"


def _a_las_12(minuto: int, segundo: int = 0) -> datetime:
    return datetime(2026, 10, 7, 12, minuto, segundo, tzinfo=UTC)


def _cliente(engine, ahora: datetime = RELOJ_FIJO) -> TestClient:
    """Cliente sin cabecera por defecto, con el reloj de la app en ``ahora``."""
    app = crear_app(engine, ConfiguracionDeSesion(SECRETO_DE_PRUEBA, rondas_bcrypt=4))
    app.dependency_overrides[get_reloj] = lambda: (lambda: ahora)
    return TestClient(app)


def _con(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _escenario(sesion) -> dict:
    consultorio = un_consultorio(sesion)
    return {
        "consultorio": consultorio,
        "paciente": un_paciente(sesion, consultorio),
        "profesional": un_profesional(sesion, consultorio),
        "sillon": un_sillon(sesion, consultorio),
        "prestacion": una_prestacion(sesion, consultorio, duracion_minutos=30),
    }


def _peticion_de_turno(datos: dict) -> dict:
    return {
        "paciente_id": datos["paciente"].id,
        "prestacion_id": datos["prestacion"].id,
        "inicio": "2026-11-02T13:00:00Z",
    }


def _cuantos(sesion, modelo) -> int:
    return sesion.scalar(select(func.count()).select_from(modelo))


# --- US-092 CA-1: toda causa de rechazo responde el mismo 401 -----------------------------------


def _cabecera_del_caso(caso: str, usuario_id: int) -> dict[str, str]:
    if caso == "sin cabecera":
        return {}
    if caso == "esquema Basic":
        return {"Authorization": "Basic dXN1YXJpbzpjbGF2ZQ=="}
    if caso == "refresh como access":
        return _con(token_de(usuario_id, tipo=TipoDeToken.REFRESH))
    if caso == "vencido":
        return _con(token_de(usuario_id))
    valido = token_de(usuario_id)  # firma alterada
    cabecera, cuerpo, firma = valido.split(".")
    alterada = ("A" if firma[3] != "A" else "B").join([firma[:3], firma[4:]])
    return _con(".".join([cabecera, cuerpo, alterada]))


CASOS_DE_401 = ["sin cabecera", "esquema Basic", "refresh como access", "vencido", "firma alterada"]


@pytest.mark.parametrize("caso", CASOS_DE_401)
def test_us092_ca1_toda_causa_de_rechazo_responde_401_rn_au_03(caso, engine, sesion) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion), roles=(Rol.ODONTOLOGO,))
    ahora = _a_las_12(15) if caso == "vencido" else RELOJ_FIJO
    cliente = _cliente(engine, ahora)

    respuesta = cliente.get("/prestaciones", headers=_cabecera_del_caso(caso, usuario.id))

    assert respuesta.status_code == 401
    assert respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    assert respuesta.headers["www-authenticate"] == "Bearer"
    assert respuesta.json()["codigos"] == ["RN-AU-03"]


def test_us092_ca1_los_cuerpos_de_todos_los_401_son_iguales(engine, sesion) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion), roles=(Rol.ODONTOLOGO,))
    respuestas = []
    for caso in CASOS_DE_401:
        ahora = _a_las_12(15) if caso == "vencido" else RELOJ_FIJO
        respuestas.append(_cliente(engine, ahora).get("/prestaciones", headers=_cabecera_del_caso(caso, usuario.id)))

    assert {r.status_code for r in respuestas} == {401}
    assert len({r.content for r in respuestas}) == 1


def test_us092_ca1_un_segundo_antes_de_vencer_responde_200(engine, sesion) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion), roles=(Rol.ODONTOLOGO,))
    cliente = _cliente(engine, _a_las_12(14, 59))

    respuesta = cliente.get("/prestaciones", headers=_con(token_de(usuario.id)))

    assert respuesta.status_code == 200


# --- US-092 CA-4: el estado del usuario se lee en cada petición ---------------------------------


def test_us092_ca4_usuario_inactivo_responde_el_mismo_401(engine, sesion) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion), roles=(Rol.ODONTOLOGO,), activo=False)
    cliente = _cliente(engine)

    respuesta = cliente.get("/prestaciones", headers=_con(token_de(usuario.id)))
    sin_token = cliente.get("/prestaciones")

    assert respuesta.status_code == 401
    assert respuesta.content == sin_token.content


def test_us092_ca4_token_version_cambiada_responde_el_mismo_401(engine, sesion) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion), roles=(Rol.ODONTOLOGO,), token_version=1)
    cliente = _cliente(engine)

    respuesta = cliente.get("/prestaciones", headers=_con(token_de(usuario.id, token_version=0)))
    sin_token = cliente.get("/prestaciones")

    assert respuesta.status_code == 401
    assert respuesta.content == sin_token.content


# --- US-091 CA-1 y CA-3: 403 con RN-AU-05 y sin efectos -----------------------------------------


def test_us091_ca3_el_dueno_no_crea_turnos(engine, sesion) -> None:
    datos = _escenario(sesion)
    dueno = un_usuario(sesion, datos["consultorio"], roles=(Rol.DUENO,))
    cliente = _cliente(engine)

    respuesta = cliente.post("/turnos", json=_peticion_de_turno(datos), headers=_con(token_de(dueno.id)))

    assert respuesta.status_code == 403
    assert respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    assert respuesta.json()["codigos"] == ["RN-AU-05"]
    assert _cuantos(sesion, TurnoModelo) == 0


def test_us091_ca3_la_recepcionista_no_crea_prestaciones(engine, sesion) -> None:
    consultorio = un_consultorio(sesion)
    recepcionista = un_usuario(sesion, consultorio, roles=(Rol.RECEPCIONISTA,))
    cliente = _cliente(engine)

    respuesta = cliente.post(
        "/prestaciones",
        json={"nombre": "Limpieza", "duracion_minutos": 30},
        headers=_con(token_de(recepcionista.id)),
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["codigos"] == ["RN-AU-05"]
    assert _cuantos(sesion, PrestacionModelo) == 0


def test_us091_ca3_un_usuario_sin_roles_no_lee_el_catalogo(engine, sesion) -> None:
    sin_roles = un_usuario(sesion, un_consultorio(sesion), roles=())
    cliente = _cliente(engine)

    respuesta = cliente.get("/prestaciones", headers=_con(token_de(sin_roles.id)))

    assert respuesta.status_code == 403
    assert respuesta.json()["codigos"] == ["RN-AU-05"]


def test_us091_ca1_la_recepcionista_si_crea_turnos(engine, sesion) -> None:
    datos = _escenario(sesion)
    recepcionista = un_usuario(sesion, datos["consultorio"], roles=(Rol.RECEPCIONISTA,))
    cliente = _cliente(engine)

    respuesta = cliente.post(
        "/turnos", json=_peticion_de_turno(datos), headers=_con(token_de(recepcionista.id))
    )

    assert respuesta.status_code == 201


# --- US-092 CA-2: la matriz de design R4 por HTTP ------------------------------------------------

# método, ruta con {turno}, {prestacion} o {sillon}, cuerpo y los roles que pasan.
RUTAS_DE_LA_MATRIZ = {
    "POST /turnos": ("POST", "/turnos", "turno_nuevo", {Rol.ODONTOLOGO, Rol.RECEPCIONISTA}),
    "GET /turnos/{id}/historial": (
        "GET", "/turnos/{turno}/historial", None, {Rol.ODONTOLOGO, Rol.RECEPCIONISTA, Rol.DUENO}
    ),
    "GET /prestaciones": ("GET", "/prestaciones", None, {Rol.ODONTOLOGO, Rol.RECEPCIONISTA, Rol.DUENO}),
    "POST /prestaciones": (
        "POST", "/prestaciones", {"nombre": "Blanqueamiento", "duracion_minutos": 30, "color": "#3A7BD5"}, {Rol.ODONTOLOGO}
    ),
    "PATCH /prestaciones/{id}": (
        "PATCH", "/prestaciones/{prestacion}", {"color": "#112233"}, {Rol.ODONTOLOGO}
    ),
    "GET /sillones": ("GET", "/sillones", None, {Rol.ODONTOLOGO, Rol.RECEPCIONISTA, Rol.DUENO}),
    "POST /sillones": ("POST", "/sillones", {"nombre": "Sillón nuevo"}, {Rol.ODONTOLOGO}),
    "PATCH /sillones/{id}": (
        "PATCH", "/sillones/{sillon}", {"nombre": "Sillón renombrado"}, {Rol.ODONTOLOGO}
    ),
}
USUARIOS_DE_LOS_EJEMPLOS = {
    "odontologa con dueno": (Rol.ODONTOLOGO, Rol.DUENO),
    "recepcionista": (Rol.RECEPCIONISTA,),
    "dueno": (Rol.DUENO,),
}


@pytest.mark.parametrize("usuario", USUARIOS_DE_LOS_EJEMPLOS)
@pytest.mark.parametrize("ruta", RUTAS_DE_LA_MATRIZ)
def test_us092_ca2_matriz_por_http(ruta, usuario, engine, sesion) -> None:
    metodo, plantilla, cuerpo, permitidos = RUTAS_DE_LA_MATRIZ[ruta]
    datos = _escenario(sesion)
    turno = un_turno(
        sesion,
        paciente=datos["paciente"], profesional=datos["profesional"], sillon=datos["sillon"],
        prestacion=datos["prestacion"], inicio=datetime(2026, 11, 3, 13, 0, tzinfo=UTC),
    )
    roles = USUARIOS_DE_LOS_EJEMPLOS[usuario]
    persona = un_usuario(sesion, datos["consultorio"], roles=roles)
    url = plantilla.format(turno=turno.id, prestacion=datos["prestacion"].id, sillon=datos["sillon"].id)
    cuerpo = _peticion_de_turno(datos) if cuerpo == "turno_nuevo" else cuerpo

    respuesta = _cliente(engine).request(metodo, url, json=cuerpo, headers=_con(token_de(persona.id)))

    if permitidos & set(roles):
        assert respuesta.status_code in (200, 201)
    else:
        assert respuesta.status_code == 403
        assert respuesta.json()["codigos"] == ["RN-AU-05"]


# --- RN-GL-02 (D208): el control de acceso va antes que la validación y que el 404 ---------------


def test_us091_ca3_403_antes_que_422_y_404(engine, sesion) -> None:
    datos = _escenario(sesion)
    dueno = un_usuario(sesion, datos["consultorio"], roles=(Rol.DUENO,))
    recepcionista = un_usuario(sesion, datos["consultorio"], roles=(Rol.RECEPCIONISTA,))
    cliente = _cliente(engine)

    con_referencia_invalida = cliente.post(
        "/turnos", json={**_peticion_de_turno(datos), "prestacion_id": 999}, headers=_con(token_de(dueno.id))
    )
    sillon_inexistente = cliente.patch(
        "/sillones/999", json={"nombre": "Nuevo"}, headers=_con(token_de(recepcionista.id))
    )

    assert (con_referencia_invalida.status_code, con_referencia_invalida.json()["codigos"]) == (403, ["RN-AU-05"])
    assert (sillon_inexistente.status_code, sillon_inexistente.json()["codigos"]) == (403, ["RN-AU-05"])


def test_us092_ca1_401_antes_que_404_y_422(engine, sesion) -> None:
    datos = _escenario(sesion)
    cliente = _cliente(engine)

    historial_inexistente = cliente.get("/turnos/999/historial")
    referencia_invalida = cliente.post("/turnos", json={**_peticion_de_turno(datos), "prestacion_id": 999})
    id_no_entero = cliente.get("/turnos/abc/historial")

    for respuesta in (historial_inexistente, referencia_invalida, id_no_entero):
        assert respuesta.status_code == 401
        assert respuesta.json()["codigos"] == ["RN-AU-03"]


def test_json_roto_sin_token_responde_422(engine) -> None:
    """El límite de design R12: FastAPI rechaza el JSON roto antes de resolver las dependencias."""
    respuesta = _cliente(engine).post(
        "/turnos", content=b'{"paciente_id": ', headers={"Content-Type": "application/json"}
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []


# --- US-091 CA-5: quitar un rol vale con el mismo token -----------------------------------------


def test_us091_ca5_quitar_un_rol_por_http(engine, sesion) -> None:
    datos = _escenario(sesion)
    usuario = un_usuario(sesion, datos["consultorio"], roles=(Rol.ODONTOLOGO, Rol.DUENO))
    cabecera = _con(token_de(usuario.id))
    cliente = _cliente(engine)
    creado = cliente.post("/turnos", json=_peticion_de_turno(datos), headers=cabecera)
    assert creado.status_code == 201

    RepositorioUsuariosSqlAlchemy(sesion).quitar_rol(usuario.id, Rol.ODONTOLOGO)
    sesion.commit()
    otro = {**_peticion_de_turno(datos), "inicio": "2026-11-02T15:00:00Z"}

    crear = cliente.post("/turnos", json=otro, headers=cabecera)
    historial = cliente.get(f"/turnos/{creado.json()['id']}/historial", headers=cabecera)

    assert (crear.status_code, crear.json()["codigos"]) == (403, ["RN-AU-05"])
    assert historial.status_code == 200


# --- design R15: OpenAPI -------------------------------------------------------------------------


def test_openapi_declara_bearer_401_y_403_en_las_rutas_protegidas(engine) -> None:
    openapi = _cliente(engine).get("/openapi.json").json()

    esquema = openapi["components"]["securitySchemes"]["AccessToken"]
    assert (esquema["type"], esquema["scheme"], esquema["bearerFormat"]) == ("http", "bearer", "JWT")
    protegidas = 0
    for ruta, operaciones in openapi["paths"].items():
        for metodo, operacion in operaciones.items():
            if ruta in ("/auth/login", "/auth/refresh"):
                assert "security" not in operacion
                continue
            protegidas += 1
            assert operacion["security"] == [{"AccessToken": []}], (metodo, ruta)
            for estado in ("401", "403"):
                contenido = operacion["responses"][estado]["content"]
                assert "application/problem+json" in contenido, (metodo, ruta, estado)
    assert protegidas == 8
