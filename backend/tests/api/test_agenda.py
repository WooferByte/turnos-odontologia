"""``GET /turnos`` y ``GET /turnos/{id}`` por HTTP con ``TestClient`` sobre ``crear_app(engine)`` (C-14, ``consulta-de-turnos``).

Sin dobles: sesión y repositorios reales sobre el engine SQLite del test, tokens reales firmados con el
secreto de los tests (D211); solo el reloj se sustituye. Cada test lleva el ID de su escenario
(AGE-1a ... AGE-3c). Datos ficticios (RN-PR-01).
"""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.api.deps import get_reloj
from app.domain.acceso.roles import Rol
from app.domain.tiempo import UTC
from app.infrastructure.configuracion import ConfiguracionDeSesion
from app.infrastructure.db.modelos import TurnoModelo
from app.main import crear_app
from tests.conftest import SECRETO_DE_PRUEBA, a_las, cabecera_de, reloj_fijo, token_de
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
    un_usuario,
)

ZONA = "America/Argentina/Buenos_Aires"
ODONTOLOGA = (Rol.ODONTOLOGO, Rol.DUENO)
RECEPCIONISTA = (Rol.RECEPCIONISTA,)
DUENO = (Rol.DUENO,)
SIN_ROLES: tuple[Rol, ...] = ()


@pytest.fixture
def reloj(engine):
    """Reloj de la app, que cada test puede mover: ``reloj["ahora"] = ...``."""
    return {"ahora": reloj_fijo()}


@pytest.fixture
def cliente(engine, reloj) -> TestClient:
    app = crear_app(engine, ConfiguracionDeSesion(SECRETO_DE_PRUEBA, rondas_bcrypt=4))
    app.dependency_overrides[get_reloj] = lambda: (lambda: reloj["ahora"])
    return TestClient(app)


def _escenario(sesion):
    consultorio = un_consultorio(sesion)
    return {
        "consultorio": consultorio,
        "profesional": un_profesional(sesion, consultorio),
        "sillon": un_sillon(sesion, consultorio),
        "ana": un_paciente(sesion, consultorio, nombre="Ana", apellido="Ejemplo"),
        "bruno": un_paciente(sesion, consultorio, nombre="Bruno", apellido="Ficticio"),
        "carla": un_paciente(sesion, consultorio, nombre="Carla", apellido="Inventada"),
        "consulta": una_prestacion(sesion, consultorio, nombre="Consulta / control", duracion_minutos=30, color="#1E88E5"),
        "limpieza": una_prestacion(sesion, consultorio, nombre="Limpieza", duracion_minutos=45, color="#43A047"),
        "obturacion": una_prestacion(sesion, consultorio, nombre="Obturación", duracion_minutos=60, color="#FB8C00"),
    }


def _turno(sesion, datos, paciente, prestacion, inicio, **kw):
    return un_turno(
        sesion,
        paciente=datos[paciente],
        profesional=datos["profesional"],
        sillon=datos["sillon"],
        prestacion=datos[prestacion],
        inicio=inicio,
        **kw,
    )


def _con(engine, roles):
    return {"headers": cabecera_de(engine, roles)}


# --- AGE-1: la agenda de un día -----------------------------------------------------------------


def test_age1a_la_odontologa_ve_el_dia_ordenado(cliente, engine, sesion):
    datos = _escenario(sesion)
    _turno(sesion, datos, "carla", "obturacion", a_las(14), estado="confirmado")
    ana = _turno(sesion, datos, "ana", "consulta", a_las(12))
    _turno(sesion, datos, "bruno", "limpieza", a_las(13))
    antes = sesion.scalar(select(func.count()).select_from(TurnoModelo))

    respuesta = cliente.get("/turnos", params={"fecha": "2026-11-02"}, **_con(engine, ODONTOLOGA))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert (cuerpo["fecha"], cuerpo["zona_horaria"]) == ("2026-11-02", ZONA)
    assert [t["paciente"]["apellido"] for t in cuerpo["turnos"]] == ["Ejemplo", "Ficticio", "Inventada"]
    assert cuerpo["turnos"][0] == {
        "id": ana.id,
        "inicio": "2026-11-02T12:00:00Z",
        "fin": "2026-11-02T12:30:00Z",
        "duracion_minutos": 30,
        "estado": "reservado",
        "profesional_id": datos["profesional"].id,
        "sillon_id": datos["sillon"].id,
        "paciente": {"id": datos["ana"].id, "nombre": "Ana", "apellido": "Ejemplo"},
        "prestacion": {"id": datos["consulta"].id, "nombre": "Consulta / control", "color": "#1E88E5"},
    }
    assert "+5491155550100" not in respuesta.text
    assert sesion.scalar(select(func.count()).select_from(TurnoModelo)) == antes


def test_age1e_la_recepcionista_y_el_dueno_leen_la_agenda(cliente, engine, sesion):
    datos = _escenario(sesion)
    _turno(sesion, datos, "ana", "consulta", a_las(12))

    de_la_recepcionista = cliente.get("/turnos?fecha=2026-11-02", **_con(engine, RECEPCIONISTA))
    del_dueno = cliente.get("/turnos?fecha=2026-11-02", **_con(engine, DUENO))

    assert (de_la_recepcionista.status_code, del_dueno.status_code) == (200, 200)
    assert de_la_recepcionista.json() == del_dueno.json()
    assert [t["paciente"]["apellido"] for t in del_dueno.json()["turnos"]] == ["Ejemplo"]


def test_age1b_el_dia_es_el_del_consultorio_no_el_de_utc(cliente, engine, sesion):
    datos = _escenario(sesion)
    _turno(sesion, datos, "ana", "consulta", datetime(2026, 11, 2, 2, 30, tzinfo=UTC))  # 23:30 del 1
    _turno(sesion, datos, "bruno", "consulta", datetime(2026, 11, 2, 3, 0, tzinfo=UTC))  # 00:00 del 2
    _turno(sesion, datos, "carla", "consulta", datetime(2026, 11, 3, 2, 30, tzinfo=UTC))  # 23:30 del 2
    cabecera = _con(engine, ODONTOLOGA)

    del_dos = cliente.get("/turnos?fecha=2026-11-02", **cabecera)
    del_uno = cliente.get("/turnos?fecha=2026-11-01", **cabecera)

    assert [t["paciente"]["apellido"] for t in del_dos.json()["turnos"]] == ["Ficticio", "Inventada"]
    assert [t["paciente"]["apellido"] for t in del_uno.json()["turnos"]] == ["Ejemplo"]


def test_age1c_sin_fecha_se_lista_el_dia_de_hoy_del_consultorio(cliente, engine, sesion, reloj):
    datos = _escenario(sesion)
    _turno(sesion, datos, "ana", "consulta", a_las(12))
    # El reloj de la app viaja a noviembre: el token tiene que seguir vigente en esa fecha.
    usuario = un_usuario(sesion, datos["consultorio"], roles=RECEPCIONISTA)
    token = token_de(usuario.id, emitido_en=datetime(2026, 11, 3, tzinfo=UTC), vigencia=timedelta(days=1))
    cabecera = {"headers": {"Authorization": f"Bearer {token}"}}

    reloj["ahora"] = datetime(2026, 11, 3, 1, 0, tzinfo=UTC)
    antes = cliente.get("/turnos", **cabecera)
    reloj["ahora"] = datetime(2026, 11, 3, 3, 0, tzinfo=UTC)
    despues = cliente.get("/turnos", **cabecera)

    assert antes.status_code == 200 and antes.json()["fecha"] == "2026-11-02"
    assert [t["paciente"]["apellido"] for t in antes.json()["turnos"]] == ["Ejemplo"]
    assert despues.json()["fecha"] == "2026-11-03"
    assert despues.json()["turnos"] == []


def test_age1d_un_turno_cancelado_y_una_prestacion_inactiva_aparecen(cliente, engine, sesion):
    datos = _escenario(sesion)
    inicio = datetime(2026, 11, 4, 13, 0, tzinfo=UTC)
    _turno(sesion, datos, "bruno", "limpieza", inicio, estado="cancelado_paciente")
    _turno(sesion, datos, "ana", "obturacion", datetime(2026, 11, 4, 15, 0, tzinfo=UTC))
    datos["obturacion"].activa = False
    sesion.commit()

    respuesta = cliente.get("/turnos?fecha=2026-11-04", **_con(engine, ODONTOLOGA))

    turnos = respuesta.json()["turnos"]
    assert [t["estado"] for t in turnos] == ["cancelado_paciente", "reservado"]
    assert turnos[1]["prestacion"] == {"id": datos["obturacion"].id, "nombre": "Obturación", "color": "#FB8C00"}


def test_age1d_un_dia_sin_turnos_da_200_con_la_lista_vacia(cliente, engine, sesion):
    _escenario(sesion)

    respuesta = cliente.get("/turnos?fecha=2026-11-05", **_con(engine, ODONTOLOGA))

    assert respuesta.status_code == 200
    assert respuesta.json() == {"fecha": "2026-11-05", "zona_horaria": ZONA, "turnos": []}


def test_age1f_a_igual_inicio_los_turnos_salen_por_id(cliente, engine, sesion):
    datos = _escenario(sesion)
    inicio = datetime(2026, 11, 4, 13, 0, tzinfo=UTC)
    _turno(sesion, datos, "ana", "limpieza", inicio, id=20)
    _turno(sesion, datos, "bruno", "limpieza", inicio, id=10, estado="cancelado_paciente")

    respuesta = cliente.get("/turnos?fecha=2026-11-04", **_con(engine, ODONTOLOGA))

    assert [(t["id"], t["paciente"]["apellido"]) for t in respuesta.json()["turnos"]] == [
        (10, "Ficticio"),
        (20, "Ejemplo"),
    ]


# --- AGE-3: entrada, acceso y consultorio -------------------------------------------------------


@pytest.mark.parametrize(
    "fecha",
    ["2026-13-01", "02/11/2026", "2026-11-02T03:00:00Z", "2026-11-02T00:00:00Z", "0001-01-01", "9999-12-31"],
)
def test_age3a_una_fecha_mal_formada_da_422_sin_codigos(cliente, engine, sesion, fecha):
    datos = _escenario(sesion)
    _turno(sesion, datos, "ana", "consulta", a_las(12))

    respuesta = cliente.get("/turnos", params={"fecha": fecha}, **_con(engine, ODONTOLOGA))

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == []
    assert [e["campo"] for e in cuerpo["errores"]] == ["fecha"]
    assert "turnos" not in cuerpo


@pytest.mark.parametrize("fecha", ["0001-01-02", "9999-12-30"])
def test_age3a_los_extremos_aceptados_dan_200_vacio(cliente, engine, sesion, fecha):
    _escenario(sesion)

    respuesta = cliente.get("/turnos", params={"fecha": fecha}, **_con(engine, ODONTOLOGA))

    assert respuesta.status_code == 200
    assert respuesta.json() == {"fecha": fecha, "zona_horaria": ZONA, "turnos": []}


def test_age3b_sin_sesion_401(cliente, sesion):
    _escenario(sesion)

    respuesta = cliente.get("/turnos?fecha=2026-11-02")

    assert respuesta.status_code == 401
    assert respuesta.json()["codigos"] == ["RN-AU-03"]


@pytest.mark.parametrize("consulta", ["fecha=2026-11-02", "fecha=mal"])
def test_age3b_sin_roles_403_antes_de_validar(cliente, engine, sesion, consulta):
    datos = _escenario(sesion)
    _turno(sesion, datos, "ana", "consulta", a_las(12))

    respuesta = cliente.get(f"/turnos?{consulta}", **_con(engine, SIN_ROLES))

    assert respuesta.status_code == 403
    assert respuesta.json()["codigos"] == ["RN-AU-05"]
    assert "Ejemplo" not in respuesta.text


def test_age3c_la_lista_no_trae_turnos_de_otro_consultorio(cliente, engine, sesion):
    datos = _escenario(sesion)
    otro = _escenario(sesion)
    _turno(sesion, datos, "ana", "consulta", a_las(12))
    _turno(sesion, otro, "bruno", "consulta", a_las(12))

    respuesta = cliente.get("/turnos?fecha=2026-11-02", **_con(engine, ODONTOLOGA))

    assert [t["paciente"]["apellido"] for t in respuesta.json()["turnos"]] == ["Ejemplo"]


# --- AGE-2: un turno por su id ------------------------------------------------------------------


def test_age2a_la_recepcionista_lee_un_turno(cliente, engine, sesion):
    datos = _escenario(sesion)
    turno = _turno(sesion, datos, "bruno", "limpieza", a_las(13))

    respuesta = cliente.get(f"/turnos/{turno.id}", **_con(engine, RECEPCIONISTA))

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "id": turno.id,
        "inicio": "2026-11-02T13:00:00Z",
        "fin": "2026-11-02T13:45:00Z",
        "duracion_minutos": 45,
        "estado": "reservado",
        "profesional_id": datos["profesional"].id,
        "sillon_id": datos["sillon"].id,
        "paciente": {"id": datos["bruno"].id, "nombre": "Bruno", "apellido": "Ficticio"},
        "prestacion": {"id": datos["limpieza"].id, "nombre": "Limpieza", "color": "#43A047"},
    }


def test_age2b_un_turno_inexistente_da_404(cliente, engine, sesion):
    _escenario(sesion)

    respuesta = cliente.get("/turnos/999", **_con(engine, ODONTOLOGA))

    assert respuesta.status_code == 404
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-GL-04"]
    assert cuerpo["referencias"] == [{"recurso": "turno", "recurso_id": 999, "motivo": "inexistente"}]


def test_age2b_un_id_no_entero_da_422(cliente, engine, sesion):
    _escenario(sesion)

    respuesta = cliente.get("/turnos/abc", **_con(engine, ODONTOLOGA))

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []


def test_age3c_un_turno_de_otro_consultorio_da_el_mismo_404(cliente, engine, sesion):
    _escenario(sesion)
    otro = _escenario(sesion)
    ajeno = _turno(sesion, otro, "bruno", "consulta", a_las(12))
    cabecera = _con(engine, ODONTOLOGA)

    del_ajeno = cliente.get(f"/turnos/{ajeno.id}", **cabecera)
    inexistente = cliente.get("/turnos/999", **cabecera)

    assert del_ajeno.status_code == inexistente.status_code == 404
    assert del_ajeno.json()["codigos"] == ["RN-GL-04"]
    assert del_ajeno.json()["referencias"][0] == {
        "recurso": "turno",
        "recurso_id": ajeno.id,
        "motivo": "inexistente",
    }
    assert del_ajeno.json()["title"] == inexistente.json()["title"]


def test_age3b_sin_roles_403_al_leer_un_turno(cliente, engine, sesion):
    _escenario(sesion)

    respuesta = cliente.get("/turnos/1", **_con(engine, SIN_ROLES))

    assert respuesta.status_code == 403
    assert respuesta.json()["codigos"] == ["RN-AU-05"]
