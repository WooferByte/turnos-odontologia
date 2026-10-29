"""``POST /turnos/{id}/cancelar`` por HTTP con ``TestClient`` sobre ``crear_app(engine)`` (C-17, ``cancelacion-de-turnos``).

Sin dobles: sesión y repositorios reales sobre el engine SQLite del test, tokens reales firmados con el
secreto de los tests (D211); solo el reloj se sustituye. Cada test lleva el ID de su escenario
(CAN-1a ... CAN-3b). Datos ficticios (RN-PR-01).
"""
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_reloj
from app.domain.acceso.roles import Rol
from app.infrastructure.configuracion import ConfiguracionDeSesion
from app.main import crear_app
from tests.conftest import RELOJ_FIJO, SECRETO_DE_PRUEBA, a_las, reloj_fijo, token_de
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
    un_usuario,
)

ODONTOLOGA = (Rol.ODONTOLOGO, Rol.DUENO)
RECEPCIONISTA = (Rol.RECEPCIONISTA,)
DUENO = (Rol.DUENO,)
SIN_ROLES: tuple[Rol, ...] = ()
TERMINALES = ["cancelado_paciente", "cancelado_profesional", "vencido", "atendido", "ausente"]
ACTIVOS = ["pendiente_aprobacion", "pendiente_sena", "reservado", "confirmado"]
CANCELACIONES = ["cancelado_paciente", "cancelado_profesional"]


@pytest.fixture
def cliente(engine) -> TestClient:
    app = crear_app(engine, ConfiguracionDeSesion(SECRETO_DE_PRUEBA, rondas_bcrypt=4))
    app.dependency_overrides[get_reloj] = lambda: reloj_fijo
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
    return {"Authorization": f"Bearer {token_de(usuario.id)}"}


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


def test_can1a_la_recepcionista_cancela_por_el_paciente(cliente, sesion):
    datos = _escenario(sesion)
    recepcionista = _usuario(sesion, datos, RECEPCIONISTA)
    cabecera = _cabecera(recepcionista)
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = cliente.post(f"/turnos/{ana['id']}/cancelar", json={"estado": "cancelado_paciente"}, headers=cabecera)

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
        "estado": "cancelado_paciente",
        "creado_en": ana["creado_en"],
    }
    del_dia = cliente.get("/turnos?fecha=2026-11-02", headers=cabecera).json()["turnos"]
    assert [(t["id"], t["inicio"], t["estado"]) for t in del_dia] == [
        (ana["id"], "2026-11-02T13:00:00Z", "cancelado_paciente")
    ]


def test_can2a_el_historial_muestra_el_cancelado(cliente, sesion):
    datos = _escenario(sesion)
    recepcionista = _usuario(sesion, datos, RECEPCIONISTA)
    cabecera = _cabecera(recepcionista)
    ana = _turno_de_ana(cliente, datos, cabecera)

    cliente.post(f"/turnos/{ana['id']}/cancelar", json={"estado": "cancelado_paciente"}, headers=cabecera)

    eventos = _historial(cliente, ana["id"], cabecera)
    assert [e["tipo"] for e in eventos] == ["creado", "cancelado"]
    cancelado = eventos[1]
    assert cancelado["ocurrido_en"] == RELOJ_FIJO.isoformat().replace("+00:00", "Z")
    assert cancelado["actor_tipo"] == "usuario"
    assert cancelado["actor_id"] == str(recepcionista.id)
    assert cancelado["antes"] == {"estado": "reservado"}
    assert cancelado["despues"] == {"estado": "cancelado_paciente"}
    assert cancelado["motivo"] is None


def test_can1a_la_odontologa_cancela_por_el_consultorio(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, ODONTOLOGA))
    bruno = _directo(sesion, datos, "bruno", 15)

    respuesta = cliente.post(f"/turnos/{bruno.id}/cancelar", json={"estado": "cancelado_profesional"}, headers=cabecera)

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "cancelado_profesional"
    assert _leer(cliente, bruno.id, cabecera)["estado"] == "cancelado_profesional"


@pytest.mark.parametrize("estado", ACTIVOS)
@pytest.mark.parametrize("pedido", CANCELACIONES)
def test_can1b_se_cancela_desde_cada_estado_activo(cliente, sesion, estado, pedido):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    bruno = _directo(sesion, datos, "bruno", 14, estado=estado)

    respuesta = cliente.post(f"/turnos/{bruno.id}/cancelar", json={"estado": pedido}, headers=cabecera)

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == pedido


def test_can1b_el_hueco_cancelado_admite_un_post_turnos(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, cabecera)
    cliente.post(f"/turnos/{ana['id']}/cancelar", json={"estado": "cancelado_profesional"}, headers=cabecera)

    nuevo = cliente.post(
        "/turnos",
        json={"paciente_id": datos["bruno"].id, "prestacion_id": datos["consulta"].id, "inicio": "2026-11-02T13:00:00Z"},
        headers=cabecera,
    )

    assert nuevo.status_code == 201
    assert nuevo.json()["estado"] == "reservado"


def test_can1b_el_hueco_cancelado_admite_un_patch(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, cabecera)
    bruno = _directo(sesion, datos, "bruno", 18)
    cliente.post(f"/turnos/{ana['id']}/cancelar", json={"estado": "cancelado_paciente"}, headers=cabecera)

    movido = cliente.patch(f"/turnos/{bruno.id}", json={"inicio": "2026-11-02T13:00:00Z"}, headers=cabecera)

    assert movido.status_code == 200
    assert movido.json()["inicio"] == "2026-11-02T13:00:00Z"


@pytest.mark.parametrize("pedido", CANCELACIONES)
@pytest.mark.parametrize("estado", TERMINALES)
def test_can1c_un_terminal_409_rn_ag_12_y_no_cambia(cliente, sesion, estado, pedido):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    terminal = _directo(sesion, datos, "ana", 13, estado=estado)
    antes = _leer(cliente, terminal.id, cabecera)

    respuesta = cliente.post(f"/turnos/{terminal.id}/cancelar", json={"estado": pedido}, headers=cabecera)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigos"] == ["RN-AG-12"]
    assert respuesta.headers["content-type"].startswith("application/problem+json")
    assert _leer(cliente, terminal.id, cabecera) == antes
    assert _historial(cliente, terminal.id, cabecera) == []


@pytest.mark.parametrize("repetida", CANCELACIONES)
def test_can1c_la_misma_cancelacion_repetida_409_y_un_solo_evento(cliente, sesion, repetida):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, cabecera)
    primera = cliente.post(f"/turnos/{ana['id']}/cancelar", json={"estado": "cancelado_paciente"}, headers=cabecera)
    assert primera.status_code == 200

    segunda = cliente.post(f"/turnos/{ana['id']}/cancelar", json={"estado": repetida}, headers=cabecera)

    assert segunda.status_code == 409
    assert segunda.json()["codigos"] == ["RN-AG-12"]
    assert _leer(cliente, ana["id"], cabecera)["estado"] == "cancelado_paciente"
    assert [e["tipo"] for e in _historial(cliente, ana["id"], cabecera)] == ["creado", "cancelado"]


def _pedido_rechazado(causa, cabecera, cabecera_del_dueno):
    return {
        "422": dict(json={"estado": "vencido"}, headers=cabecera),
        "403": dict(json={"estado": "cancelado_paciente"}, headers=cabecera_del_dueno),
        "401": dict(json={"estado": "cancelado_paciente"}),
    }[causa]


@pytest.mark.parametrize(("causa", "esperado"), [("422", 422), ("403", 403), ("401", 401)])
def test_can2b_un_rechazo_no_registra_eventos(cliente, sesion, causa, esperado):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, cabecera)
    pedido = _pedido_rechazado(causa, cabecera, _cabecera(_usuario(sesion, datos, DUENO)))

    respuesta = cliente.post(f"/turnos/{ana['id']}/cancelar", **pedido)

    assert respuesta.status_code == esperado
    assert [e["tipo"] for e in _historial(cliente, ana["id"], cabecera)] == ["creado"]
    assert _leer(cliente, ana["id"], cabecera)["estado"] == "reservado"


def test_can2b_el_409_de_un_atendido_no_registra_eventos(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    atendido = _directo(sesion, datos, "ana", 15, estado="atendido")

    respuesta = cliente.post(f"/turnos/{atendido.id}/cancelar", json={"estado": "cancelado_paciente"}, headers=cabecera)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigos"] == ["RN-AG-12"]
    assert _historial(cliente, atendido.id, cabecera) == []
    assert _leer(cliente, atendido.id, cabecera)["estado"] == "atendido"


def test_can3a_sin_sesion_401(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = cliente.post(f"/turnos/{ana['id']}/cancelar", json={"estado": "cancelado_paciente"})

    assert respuesta.status_code == 401
    assert respuesta.json()["codigos"] == ["RN-AU-03"]
    assert _leer(cliente, ana["id"], cabecera)["estado"] == "reservado"


@pytest.mark.parametrize("roles", [DUENO, SIN_ROLES])
@pytest.mark.parametrize(
    ("de_otro", "cuerpo"),
    [(False, {"estado": "cancelado_paciente"}), (False, {"estado": "vencido"}), (True, {"estado": "cancelado_paciente"})],
)
def test_can3a_el_dueno_y_sin_roles_403_antes_de_validar(cliente, sesion, roles, de_otro, cuerpo):
    datos = _escenario(sesion)
    recepcionista = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, recepcionista)
    cabecera = _cabecera(_usuario(sesion, datos, roles))
    turno_id = 999 if de_otro else ana["id"]

    respuesta = cliente.post(f"/turnos/{turno_id}/cancelar", json=cuerpo, headers=cabecera)

    assert respuesta.status_code == 403
    assert respuesta.json()["codigos"] == ["RN-AU-05"]
    assert _leer(cliente, ana["id"], recepcionista)["estado"] == "reservado"


def test_can3b_inexistente_y_de_otro_consultorio_404_sin_distinguir(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    otro = _escenario(sesion)
    ajeno = _directo(sesion, otro, "ana", 13)
    cuerpo = {"estado": "cancelado_paciente"}

    inexistente = cliente.post("/turnos/999/cancelar", json=cuerpo, headers=cabecera)
    del_otro = cliente.post(f"/turnos/{ajeno.id}/cancelar", json=cuerpo, headers=cabecera)

    assert inexistente.status_code == del_otro.status_code == 404
    assert inexistente.json()["codigos"] == del_otro.json()["codigos"] == ["RN-GL-04"]
    assert inexistente.json()["referencias"] == [{"recurso": "turno", "recurso_id": 999, "motivo": "inexistente"}]
    assert del_otro.json()["referencias"] == [{"recurso": "turno", "recurso_id": ajeno.id, "motivo": "inexistente"}]
    assert inexistente.json()["title"] == del_otro.json()["title"]
    sesion.expire_all()
    assert ajeno.estado == "reservado"


@pytest.mark.parametrize(
    "cuerpo",
    [
        {},
        {"estado": "cancelado_consultorio"},
        {"estado": "atendido"},
        {"estado": None},
        {"estado": "cancelado_paciente", "motivo": "Viaje"},
        {"estado": 1},
    ],
)
def test_can3b_peticion_mal_formada_422_sin_codigos(cliente, sesion, cuerpo):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = cliente.post(f"/turnos/{ana['id']}/cancelar", json=cuerpo, headers=cabecera)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []
    assert respuesta.json()["errores"][0]["campo"] is not None
    assert _leer(cliente, ana["id"], cabecera)["estado"] == "reservado"


def test_can3b_sin_cuerpo_422(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = cliente.post(f"/turnos/{ana['id']}/cancelar", headers=cabecera)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []
    assert _leer(cliente, ana["id"], cabecera)["estado"] == "reservado"


def test_can3b_un_id_que_no_es_entero_422(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))

    respuesta = cliente.post("/turnos/abc/cancelar", json={"estado": "cancelado_paciente"}, headers=cabecera)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []


def test_can3b_el_formato_va_antes_que_el_404(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(_usuario(sesion, datos, RECEPCIONISTA))

    respuesta = cliente.post("/turnos/999/cancelar", json={"estado": "atendido"}, headers=cabecera)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []
