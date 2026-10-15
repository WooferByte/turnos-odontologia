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
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
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
