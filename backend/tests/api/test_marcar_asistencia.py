"""``POST /turnos/{id}/estado`` por HTTP con ``TestClient`` sobre ``crear_app(engine)`` (C-18, ``marcado-de-asistencia``).

Sin dobles: sesión y repositorios reales sobre el engine SQLite del test, tokens reales firmados con el
secreto de los tests (D211); solo el reloj se sustituye, fijo en 2026-11-02T13:10:00Z (10 minutos después
del turno de las 13:00). Cada test lleva el ID de su escenario (ASI-1a ... ASI-4b). Datos ficticios (RN-PR-01).
"""
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update

from app.api.deps import get_reloj
from app.domain.acceso.roles import Rol
from app.infrastructure.configuracion import ConfiguracionDeSesion
from app.infrastructure.db.modelos import PrestacionModelo, ProfesionalModelo, SillonModelo
from app.main import crear_app
from tests.conftest import SECRETO_DE_PRUEBA, a_las, token_de
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
    un_usuario,
)

AHORA = datetime(2026, 11, 2, 13, 10, tzinfo=UTC)
VIGENCIA_LARGA = timedelta(days=90)  # el reloj de los tests está semanas después de RELOJ_FIJO, que emite los tokens
UN_SEGUNDO_ANTES = datetime(2026, 11, 2, 12, 59, 59, tzinfo=UTC)
ODONTOLOGA = (Rol.ODONTOLOGO, Rol.DUENO)
RECEPCIONISTA = (Rol.RECEPCIONISTA,)
DUENO = (Rol.DUENO,)
SIN_ROLES: tuple[Rol, ...] = ()
NO_SE_MARCAN = [
    "pendiente_aprobacion",
    "pendiente_sena",
    "cancelado_paciente",
    "cancelado_profesional",
    "vencido",
    "atendido",
    "ausente",
]
MARCADOS = ["atendido", "ausente"]


@pytest.fixture
def reloj() -> dict:
    """El reloj de la API, que cada test puede mover."""
    return {"ahora": AHORA}


@pytest.fixture
def cliente(engine, reloj) -> TestClient:
    app = crear_app(engine, ConfiguracionDeSesion(SECRETO_DE_PRUEBA, rondas_bcrypt=4))
    app.dependency_overrides[get_reloj] = lambda: lambda: reloj["ahora"]
    return TestClient(app)


def _escenario(sesion) -> dict:
    consultorio = un_consultorio(sesion)
    return {
        "consultorio": consultorio,
        "profesional": un_profesional(sesion, consultorio),
        "sillon": un_sillon(sesion, consultorio),
        "ana": un_paciente(sesion, consultorio, nombre="Ana", apellido="Ejemplo"),
        "bruno": un_paciente(sesion, consultorio, nombre="Bruno", apellido="Ficticio"),
        "consulta": una_prestacion(sesion, consultorio, nombre="Consulta / control", duracion_minutos=30),
        "limpieza": una_prestacion(sesion, consultorio, nombre="Limpieza", duracion_minutos=45),
    }


def _usuario(sesion, datos, roles):
    return un_usuario(sesion, datos["consultorio"], roles=roles)


def _cabecera(usuario) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_de(usuario.id, vigencia=VIGENCIA_LARGA)}"}


def _turno_de_ana(cliente, datos, cabecera, hora=13) -> dict:
    """El turno de Ana creado con ``POST /turnos`` (con su evento ``creado``)."""
    respuesta = cliente.post(
        "/turnos",
        json={
            "paciente_id": datos["ana"].id,
            "prestacion_id": datos["consulta"].id,
            "inicio": a_las(hora).isoformat().replace("+00:00", "Z"),
        },
        headers=cabecera,
    )
    assert respuesta.status_code == 201
    return respuesta.json()


def _directo(sesion, datos, paciente, hora, minuto=0, estado="reservado", prestacion="consulta"):
    return un_turno(
        sesion,
        paciente=datos[paciente],
        profesional=datos["profesional"],
        sillon=datos["sillon"],
        prestacion=datos[prestacion],
        inicio=a_las(hora, minuto),
        estado=estado,
    )


def _leer(cliente, turno_id, cabecera) -> dict:
    return cliente.get(f"/turnos/{turno_id}", headers=cabecera).json()


def _historial(cliente, turno_id, cabecera) -> list[dict]:
    return cliente.get(f"/turnos/{turno_id}/historial", headers=cabecera).json()


def _marcar(cliente, turno_id, estado, cabecera):
    return cliente.post(f"/turnos/{turno_id}/estado", json={"estado": estado}, headers=cabecera)


def test_asi1a_la_recepcionista_marca_atendido(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = _marcar(cliente, ana["id"], "atendido", cabecera)

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "id": ana["id"],
        "consultorio_id": datos["consultorio"].id,
        "paciente_id": datos["ana"].id,
        "profesional_id": datos["profesional"].id,
        "sillon_id": datos["sillon"].id,
        "prestacion_id": datos["consulta"].id,
        "inicio": "2026-11-02T13:00:00Z",
        "fin": "2026-11-02T13:30:00Z",
        "duracion_minutos": 30,
        "estado": "atendido",
        "creado_en": ana["creado_en"],
    }
    del_dia = cliente.get("/turnos?fecha=2026-11-02", headers=cabecera).json()["turnos"]
    assert [(t["id"], t["inicio"], t["estado"]) for t in del_dia] == [(ana["id"], "2026-11-02T13:00:00Z", "atendido")]


def test_asi2a_el_historial_muestra_el_estado_cambiado(cliente, sesion):
    datos = _escenario(sesion)
    recepcionista = _usuario(sesion, datos, RECEPCIONISTA)
    cabecera = _cabecera(recepcionista)
    ana = _turno_de_ana(cliente, datos, cabecera)

    _marcar(cliente, ana["id"], "atendido", cabecera)

    eventos = _historial(cliente, ana["id"], cabecera)
    assert [e["tipo"] for e in eventos] == ["creado", "estado_cambiado"]
    cambio = eventos[1]
    assert cambio["ocurrido_en"] == "2026-11-02T13:10:00Z"
    assert cambio["actor_tipo"] == "usuario"
    assert cambio["actor_id"] == str(recepcionista.id)
    assert cambio["antes"] == {"estado": "reservado"}
    assert cambio["despues"] == {"estado": "atendido"}
    assert cambio["motivo"] is None


def test_asi1a_la_odontologa_marca_ausente(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, ODONTOLOGA))
    bruno = _directo(sesion, datos, "bruno", 12, estado="confirmado")

    respuesta = _marcar(cliente, bruno.id, "ausente", cabecera)

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "ausente"
    assert _leer(cliente, bruno.id, cabecera)["estado"] == "ausente"


def test_asi1b_el_hueco_marcado_admite_un_post_turnos(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, cabecera)
    _marcar(cliente, ana["id"], "ausente", cabecera)

    nuevo = cliente.post(
        "/turnos",
        json={"paciente_id": datos["bruno"].id, "prestacion_id": datos["consulta"].id, "inicio": "2026-11-02T13:00:00Z"},
        headers=cabecera,
    )

    assert nuevo.status_code == 201
    assert nuevo.json()["estado"] == "reservado"


@pytest.mark.parametrize("pedido", MARCADOS)
@pytest.mark.parametrize("estado", NO_SE_MARCAN)
def test_asi1c_un_estado_que_no_se_marca_409_rn_ag_12_y_no_cambia(cliente, sesion, estado, pedido):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    turno = _directo(sesion, datos, "ana", 13, estado=estado)
    antes = _leer(cliente, turno.id, cabecera)

    respuesta = _marcar(cliente, turno.id, pedido, cabecera)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigos"] == ["RN-AG-12"]
    assert respuesta.headers["content-type"].startswith("application/problem+json")
    assert _leer(cliente, turno.id, cabecera) == antes
    assert _historial(cliente, turno.id, cabecera) == []


@pytest.mark.parametrize("repetido", MARCADOS)
def test_asi1c_el_marcado_repetido_y_el_contrario_409_y_un_solo_evento(cliente, sesion, repetido):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, cabecera)
    assert _marcar(cliente, ana["id"], "atendido", cabecera).status_code == 200

    segundo = _marcar(cliente, ana["id"], repetido, cabecera)

    assert segundo.status_code == 409
    assert segundo.json()["codigos"] == ["RN-AG-12"]
    assert _leer(cliente, ana["id"], cabecera)["estado"] == "atendido"
    assert [e["tipo"] for e in _historial(cliente, ana["id"], cabecera)] == ["creado", "estado_cambiado"]


def test_asi1f_recursos_desactivados_despues_200(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, cabecera)
    for modelo, clave, campo in (
        (ProfesionalModelo, "profesional", "activo"),
        (SillonModelo, "sillon", "activo"),
        (PrestacionModelo, "consulta", "activa"),
    ):
        sesion.execute(update(modelo).where(modelo.id == datos[clave].id).values(**{campo: False}))
    sesion.commit()

    respuesta = _marcar(cliente, ana["id"], "atendido", cabecera)

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "atendido"


@pytest.mark.parametrize("estado", ["reservado", "confirmado"])
def test_asi1d_antes_del_inicio_409_rn_ag_13(cliente, sesion, reloj, estado):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    turno = _directo(sesion, datos, "ana", 13, estado=estado)
    reloj["ahora"] = UN_SEGUNDO_ANTES

    respuesta = _marcar(cliente, turno.id, "atendido", cabecera)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigos"] == ["RN-AG-13"]
    assert respuesta.json()["type"].endswith("/errores/marcado-antes-del-inicio")
    assert _leer(cliente, turno.id, cabecera)["estado"] == estado
    assert _historial(cliente, turno.id, cabecera) == []


def test_asi1d_en_el_segundo_exacto_del_inicio_200(cliente, sesion, reloj):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    turno = _directo(sesion, datos, "ana", 13)
    reloj["ahora"] = a_las(13)

    assert _marcar(cliente, turno.id, "atendido", cabecera).status_code == 200


def test_asi1d_un_cancelado_futuro_409_rn_ag_12_y_no_rn_ag_13(cliente, sesion, reloj):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    turno = _directo(sesion, datos, "ana", 13, estado="cancelado_paciente")
    reloj["ahora"] = UN_SEGUNDO_ANTES

    respuesta = _marcar(cliente, turno.id, "atendido", cabecera)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigos"] == ["RN-AG-12"]


def _pedido_rechazado(causa, cabecera, cabecera_del_dueno):
    return {
        "422": dict(json={"estado": "reservado"}, headers=cabecera),
        "403": dict(json={"estado": "atendido"}, headers=cabecera_del_dueno),
        "401": dict(json={"estado": "atendido"}),
    }[causa]


@pytest.mark.parametrize(("causa", "esperado"), [("422", 422), ("403", 403), ("401", 401)])
def test_asi2b_un_rechazo_no_registra_eventos(cliente, sesion, causa, esperado):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, cabecera)
    pedido = _pedido_rechazado(causa, cabecera, _cabecera(_usuario(sesion, datos, DUENO)))

    respuesta = cliente.post(f"/turnos/{ana['id']}/estado", **pedido)

    assert respuesta.status_code == esperado
    assert [e["tipo"] for e in _historial(cliente, ana["id"], cabecera)] == ["creado"]
    assert _leer(cliente, ana["id"], cabecera)["estado"] == "reservado"


def test_asi2b_el_409_de_rn_ag_13_no_registra_eventos(cliente, sesion, reloj):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, cabecera)
    reloj["ahora"] = UN_SEGUNDO_ANTES

    respuesta = _marcar(cliente, ana["id"], "atendido", cabecera)

    assert respuesta.status_code == 409
    assert [e["tipo"] for e in _historial(cliente, ana["id"], cabecera)] == ["creado"]
    assert _leer(cliente, ana["id"], cabecera)["estado"] == "reservado"


def test_asi2b_el_409_de_rn_ag_12_no_registra_eventos(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    atendido = _directo(sesion, datos, "ana", 12, estado="atendido")

    respuesta = _marcar(cliente, atendido.id, "ausente", cabecera)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigos"] == ["RN-AG-12"]
    assert _historial(cliente, atendido.id, cabecera) == []
    assert _leer(cliente, atendido.id, cabecera)["estado"] == "atendido"


def test_asi4a_sin_sesion_401(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = cliente.post(f"/turnos/{ana['id']}/estado", json={"estado": "atendido"})

    assert respuesta.status_code == 401
    assert respuesta.json()["codigos"] == ["RN-AU-03"]
    assert _leer(cliente, ana["id"], cabecera)["estado"] == "reservado"


@pytest.mark.parametrize("roles", [DUENO, SIN_ROLES])
@pytest.mark.parametrize(
    ("de_otro", "cuerpo"),
    [(False, {"estado": "atendido"}), (False, {"estado": "cancelado_paciente"}), (True, {"estado": "atendido"})],
)
def test_asi4a_el_dueno_y_sin_roles_403_antes_de_validar(cliente, sesion, roles, de_otro, cuerpo):
    datos = _escenario(sesion)
    recepcionista = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, recepcionista)
    cabecera = _cabecera(_usuario(sesion, datos, roles))
    turno_id = 999 if de_otro else ana["id"]

    respuesta = cliente.post(f"/turnos/{turno_id}/estado", json=cuerpo, headers=cabecera)

    assert respuesta.status_code == 403
    assert respuesta.json()["codigos"] == ["RN-AU-05"]
    assert _leer(cliente, ana["id"], recepcionista)["estado"] == "reservado"


def test_asi4b_inexistente_y_de_otro_consultorio_404_sin_distinguir(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    otro = _escenario(sesion)
    ajeno = _directo(sesion, otro, "ana", 13)

    inexistente = _marcar(cliente, 999, "atendido", cabecera)
    del_otro = _marcar(cliente, ajeno.id, "atendido", cabecera)

    assert inexistente.status_code == del_otro.status_code == 404
    assert inexistente.json()["codigos"] == del_otro.json()["codigos"] == ["RN-GL-04"]
    assert inexistente.json()["referencias"] == [{"recurso": "turno", "recurso_id": 999, "motivo": "inexistente"}]
    assert del_otro.json()["referencias"] == [{"recurso": "turno", "recurso_id": ajeno.id, "motivo": "inexistente"}]
    sesion.expire_all()
    assert ajeno.estado == "reservado"


@pytest.mark.parametrize(
    "cuerpo",
    [
        {},
        {"estado": "reservado"},
        {"estado": "cancelado_paciente"},
        {"estado": "Atendido"},
        {"estado": None},
        {"estado": "atendido", "motivo": "Llegó tarde"},
        {"estado": 1},
    ],
)
def test_asi4b_peticion_mal_formada_422_sin_codigos(cliente, sesion, cuerpo):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = cliente.post(f"/turnos/{ana['id']}/estado", json=cuerpo, headers=cabecera)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []
    assert respuesta.json()["errores"][0]["campo"] is not None
    assert _leer(cliente, ana["id"], cabecera)["estado"] == "reservado"


def test_asi4b_sin_cuerpo_422(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = cliente.post(f"/turnos/{ana['id']}/estado", headers=cabecera)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []


def test_asi4b_un_id_que_no_es_entero_422(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))

    respuesta = cliente.post("/turnos/abc/estado", json={"estado": "atendido"}, headers=cabecera)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []


def test_asi4b_el_formato_va_antes_que_el_404(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))

    respuesta = cliente.post("/turnos/999/estado", json={"estado": "cancelado_paciente"}, headers=cabecera)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []
