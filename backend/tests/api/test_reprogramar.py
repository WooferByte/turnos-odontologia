"""``PATCH /turnos/{id}`` por HTTP con ``TestClient`` sobre ``crear_app(engine)`` (C-16, ``reprogramacion-de-turnos``).

Sin dobles: sesión y repositorios reales sobre el engine SQLite del test, tokens reales firmados con el
secreto de los tests (D211); solo el reloj se sustituye. Cada test lleva el ID de su escenario
(REP-1a ... REP-5b). Datos ficticios (RN-PR-01).
"""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update

from app.api.deps import get_reloj
from app.domain.acceso.roles import Rol
from app.domain.tiempo import UTC
from app.infrastructure.configuracion import ConfiguracionDeSesion
from app.infrastructure.db.modelos import TurnoModelo
from app.main import crear_app
from tests.conftest import RELOJ_FIJO, SECRETO_DE_PRUEBA, a_las, reloj_fijo, token_de
from tests.factories import (
    franja,
    un_bloqueo,
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


@pytest.fixture
def cliente(engine) -> TestClient:
    app = crear_app(engine, ConfiguracionDeSesion(SECRETO_DE_PRUEBA, rondas_bcrypt=4))
    app.dependency_overrides[get_reloj] = lambda: reloj_fijo
    return TestClient(app)


HORARIO_8_A_20 = tuple(franja(dia, "08:00", "20:00") for dia in range(5))  # lunes a viernes


def _escenario(sesion, **kw) -> dict:
    consultorio = un_consultorio(sesion)
    return {
        "consultorio": consultorio,
        "profesional": un_profesional(sesion, consultorio, **kw),
        "sillon": un_sillon(sesion, consultorio),
        "ana": un_paciente(sesion, consultorio, nombre="Ana", apellido="Ejemplo"),
        "bruno": un_paciente(sesion, consultorio, nombre="Bruno", apellido="Ficticio"),
        "consulta": una_prestacion(sesion, consultorio, nombre="Consulta / control", duracion_minutos=30),
        "limpieza": una_prestacion(sesion, consultorio, nombre="Limpieza", duracion_minutos=45),
    }


def _cabecera(sesion, datos, roles) -> dict[str, str]:
    usuario = un_usuario(sesion, datos["consultorio"], roles=roles)
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


def _de_bruno(sesion, datos, hora, minuto=0, estado="reservado", prestacion="limpieza"):
    return un_turno(
        sesion,
        paciente=datos["bruno"],
        profesional=datos["profesional"],
        sillon=datos["sillon"],
        prestacion=datos[prestacion],
        inicio=a_las(hora, minuto),
        estado=estado,
    )


def _leer(cliente, turno_id, cabecera) -> dict:
    return cliente.get(f"/turnos/{turno_id}", headers=cabecera).json()


def _tipos(cliente, turno_id, cabecera) -> list[str]:
    return [e["tipo"] for e in cliente.get(f"/turnos/{turno_id}/historial", headers=cabecera).json()]


def test_rep1a_la_recepcionista_mueve_un_turno(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = cliente.patch(f"/turnos/{ana['id']}", json={"inicio": "2026-11-02T17:00:00Z"}, headers=cabecera)

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "id": ana["id"],
        "consultorio_id": datos["consultorio"].id,
        "paciente_id": datos["ana"].id,
        "profesional_id": datos["profesional"].id,
        "sillon_id": datos["sillon"].id,
        "prestacion_id": datos["consulta"].id,
        "inicio": "2026-11-02T17:00:00Z",
        "fin": "2026-11-02T17:30:00Z",
        "duracion_minutos": 30,
        "estado": "reservado",
        "creado_en": ana["creado_en"],
    }
    del_dia = cliente.get("/turnos?fecha=2026-11-02", headers=cabecera).json()["turnos"]
    assert [(t["id"], t["inicio"]) for t in del_dia] == [(ana["id"], "2026-11-02T17:00:00Z")]
    assert sesion.scalar(select(func.count()).select_from(TurnoModelo)) == 1


def test_rep2a_el_historial_muestra_el_reprogramado(cliente, sesion):
    datos = _escenario(sesion)
    usuario = un_usuario(sesion, datos["consultorio"], roles=RECEPCIONISTA)
    cabecera = {"Authorization": f"Bearer {token_de(usuario.id)}"}
    ana = _turno_de_ana(cliente, datos, cabecera)

    cliente.patch(
        f"/turnos/{ana['id']}", json={"inicio": "2026-11-02T17:00:00Z", "duracion_minutos": 45}, headers=cabecera
    )

    eventos = cliente.get(f"/turnos/{ana['id']}/historial", headers=cabecera).json()
    assert [e["tipo"] for e in eventos] == ["creado", "reprogramado"]
    reprogramado = eventos[1]
    assert reprogramado["ocurrido_en"] == RELOJ_FIJO.isoformat().replace("+00:00", "Z")
    assert reprogramado["actor_tipo"] == "usuario"
    assert reprogramado["actor_id"] == str(usuario.id)
    assert reprogramado["antes"] == {
        "inicio": "2026-11-02T13:00:00Z", "fin": "2026-11-02T13:30:00Z", "duracion_minutos": 30,
    }
    assert reprogramado["despues"] == {
        "inicio": "2026-11-02T17:00:00Z", "fin": "2026-11-02T17:45:00Z", "duracion_minutos": 45,
    }
    assert reprogramado["motivo"] is None


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


def _horario_del_turno(cliente, turno_id, cabecera):
    t = _leer(cliente, turno_id, cabecera)
    return t["inicio"], t["fin"], t["duracion_minutos"], t["estado"]


ANA_13 = ("2026-11-02T13:00:00Z", "2026-11-02T13:30:00Z", 30, "reservado")


def test_rep1a_la_odontologa_tambien_reprograma(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, ODONTOLOGA)
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = cliente.patch(f"/turnos/{ana['id']}", json={"inicio": "2026-11-02T17:00:00Z"}, headers=cabecera)

    assert respuesta.status_code == 200
    assert respuesta.json()["inicio"] == "2026-11-02T17:00:00Z"


def test_rep1c_sobre_otro_turno_activo_409_con_los_dos_conflictos_y_no_cambia(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    ana = _turno_de_ana(cliente, datos, cabecera)
    bruno = _de_bruno(sesion, datos, 14, estado="confirmado")

    respuesta = cliente.patch(f"/turnos/{ana['id']}", json={"inicio": "2026-11-02T14:15:00Z"}, headers=cabecera)

    assert respuesta.status_code == 409
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-AG-05", "RN-AG-08"]
    assert cuerpo["conflictos"] == [
        {"codigo": "RN-AG-05", "recurso": "profesional", "recurso_id": datos["profesional"].id, "turno_id": bruno.id},
        {"codigo": "RN-AG-08", "recurso": "sillon", "recurso_id": datos["sillon"].id, "turno_id": bruno.id},
    ]
    assert _horario_del_turno(cliente, ana["id"], cabecera) == ANA_13
    assert _tipos(cliente, ana["id"], cabecera) == ["creado"]


def test_rep1c_un_turno_cancelado_libera_el_horario(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    ana = _turno_de_ana(cliente, datos, cabecera)
    _de_bruno(sesion, datos, 14, estado="cancelado_paciente")

    respuesta = cliente.patch(f"/turnos/{ana['id']}", json={"inicio": "2026-11-02T14:15:00Z"}, headers=cabecera)

    assert respuesta.status_code == 200
    assert (respuesta.json()["inicio"], respuesta.json()["fin"]) == ("2026-11-02T14:15:00Z", "2026-11-02T14:45:00Z")


@pytest.mark.parametrize(
    ("inicio", "codigo"),
    [
        ("2026-11-03T02:45:00Z", "RN-AG-10d"),
        ("2026-11-02T10:30:00Z", "RN-AG-04"),
        ("2026-11-07T13:00:00Z", "RN-AG-04"),
        ("2026-11-03T13:00:00Z", "RN-AG-04b"),
    ],
)
def test_rep1d_las_reglas_de_un_turno_nuevo_dan_422_de_a_una(cliente, sesion, inicio, codigo):
    datos = _escenario(sesion, horario=HORARIO_8_A_20)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    ana = _turno_de_ana(cliente, datos, cabecera)
    bloqueo = un_bloqueo(
        sesion, datos["consultorio"], inicio=datetime(2026, 11, 3, 12, tzinfo=UTC), fin=datetime(2026, 11, 3, 15, tzinfo=UTC)
    )

    respuesta = cliente.patch(f"/turnos/{ana['id']}", json={"inicio": inicio}, headers=cabecera)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == [codigo]
    if codigo == "RN-AG-04b":
        assert respuesta.json()["bloqueo_id"] == bloqueo.id
    assert _horario_del_turno(cliente, ana["id"], cabecera) == ANA_13


def test_rep1d_horario_y_solapamiento_a_la_vez_solo_informa_el_horario(cliente, sesion):
    datos = _escenario(sesion, horario=HORARIO_8_A_20)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    ana = _turno_de_ana(cliente, datos, cabecera)
    _directo(sesion, datos, "bruno", 10, 30)  # 07:30 a 08:00 del consultorio, guardado sin regla (D261)

    respuesta = cliente.patch(f"/turnos/{ana['id']}", json={"inicio": "2026-11-02T10:30:00Z"}, headers=cabecera)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == ["RN-AG-04"]
    assert "conflictos" not in respuesta.json()


def test_rep3a_alargar_sin_mover(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, ODONTOLOGA)
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = cliente.patch(f"/turnos/{ana['id']}", json={"duracion_minutos": 60}, headers=cabecera)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert (cuerpo["inicio"], cuerpo["fin"], cuerpo["duracion_minutos"]) == (
        "2026-11-02T13:00:00Z", "2026-11-02T14:00:00Z", 60,
    )
    assert datos["consulta"].duracion_minutos == 30


def test_rep3a_alargar_contra_el_turno_siguiente_409(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, ODONTOLOGA)
    ana = _turno_de_ana(cliente, datos, cabecera)
    _directo(sesion, datos, "bruno", 13, 45)

    respuesta = cliente.patch(f"/turnos/{ana['id']}", json={"duracion_minutos": 60}, headers=cabecera)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigos"] == ["RN-AG-05", "RN-AG-08"]
    assert _horario_del_turno(cliente, ana["id"], cabecera) == ANA_13


@pytest.mark.parametrize("duracion", [42, 0, -5])
def test_rep3b_una_duracion_invalida_da_422_rn_ag_01_con_el_error_del_campo(cliente, sesion, duracion):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = cliente.patch(f"/turnos/{ana['id']}", json={"duracion_minutos": duracion}, headers=cabecera)

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-AG-01"]
    assert [(e["campo"], e["codigo"]) for e in cuerpo["errores"]] == [("duracion_minutos", "RN-AG-01")]
    assert _horario_del_turno(cliente, ana["id"], cabecera) == ANA_13


def test_rep3b_inicio_sin_zona_y_duracion_invalida_dan_un_unico_422_con_los_dos_codigos(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = cliente.patch(
        f"/turnos/{ana['id']}", json={"inicio": "2026-11-02T14:00:00", "duracion_minutos": 42}, headers=cabecera
    )

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-GL-01", "RN-AG-01"]
    assert [e["campo"] for e in cuerpo["errores"]] == ["inicio", "duracion_minutos"]


def test_rep3b_cinco_minutos_es_valida(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = cliente.patch(f"/turnos/{ana['id']}", json={"duracion_minutos": 5}, headers=cabecera)

    assert respuesta.status_code == 200
    assert respuesta.json()["fin"] == "2026-11-02T13:05:00Z"


@pytest.mark.parametrize("duracion", [1445, 1_000_000_000])
def test_rep3c_una_duracion_desmedida_422_nunca_500(cliente, sesion, duracion):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = cliente.patch(f"/turnos/{ana['id']}", json={"duracion_minutos": duracion}, headers=cabecera)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == ["RN-AG-01"]
    assert _horario_del_turno(cliente, ana["id"], cabecera) == ANA_13
    assert _tipos(cliente, ana["id"], cabecera) == ["creado"]


def test_rep3c_1440_da_rn_ag_10d_y_no_rn_ag_01(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = cliente.patch(f"/turnos/{ana['id']}", json={"duracion_minutos": 1440}, headers=cabecera)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == ["RN-AG-10d"]


def test_rep4a_sin_sesion_401(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = cliente.patch(f"/turnos/{ana['id']}", json={"inicio": "2026-11-02T17:00:00Z"})

    assert respuesta.status_code == 401
    assert respuesta.json()["codigos"] == ["RN-AU-03"]
    assert _horario_del_turno(cliente, ana["id"], cabecera) == ANA_13


@pytest.mark.parametrize("roles", [DUENO, SIN_ROLES])
@pytest.mark.parametrize(
    ("ruta_de_otro", "cuerpo"),
    [(False, {"inicio": "2026-11-02T17:00:00Z"}), (False, {"inicio": "mal"}), (True, {"inicio": "2026-11-02T17:00:00Z"})],
)
def test_rep4a_el_dueno_y_sin_roles_403_antes_de_validar(cliente, sesion, roles, ruta_de_otro, cuerpo):
    datos = _escenario(sesion)
    ana = _turno_de_ana(cliente, datos, _cabecera(sesion, datos, RECEPCIONISTA))
    cabecera = _cabecera(sesion, datos, roles)
    turno_id = 999 if ruta_de_otro else ana["id"]

    respuesta = cliente.patch(f"/turnos/{turno_id}", json=cuerpo, headers=cabecera)

    assert respuesta.status_code == 403
    assert respuesta.json()["codigos"] == ["RN-AU-05"]
    assert _horario_del_turno(cliente, ana["id"], _cabecera(sesion, datos, ODONTOLOGA)) == ANA_13


def test_rep4b_inexistente_y_de_otro_consultorio_404_sin_distinguir(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    _turno_de_ana(cliente, datos, cabecera)
    otro = _escenario(sesion)
    ajeno = _directo(sesion, otro, "ana", 13)

    inexistente = cliente.patch("/turnos/999", json={"inicio": "2026-11-02T17:00:00Z"}, headers=cabecera)
    del_otro = cliente.patch(f"/turnos/{ajeno.id}", json={"inicio": "2026-11-02T17:00:00Z"}, headers=cabecera)

    assert inexistente.status_code == del_otro.status_code == 404
    assert inexistente.json()["codigos"] == del_otro.json()["codigos"] == ["RN-GL-04"]
    assert inexistente.json()["referencias"] == [{"recurso": "turno", "recurso_id": 999, "motivo": "inexistente"}]
    assert del_otro.json()["referencias"] == [{"recurso": "turno", "recurso_id": ajeno.id, "motivo": "inexistente"}]
    assert inexistente.json()["title"] == del_otro.json()["title"]
    assert sesion.get(TurnoModelo, ajeno.id).inicio.replace(tzinfo=None) == a_las(13).replace(tzinfo=None)


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"inicio": "2026-11-02T17:00:00Z", "sillon_id": 2},
        {"inicio": None},
        {"duracion_minutos": None},
        {"duracion_minutos": "media hora"},
        {"inicio": "mañana"},
    ],
)
def test_rep4b_un_cuerpo_mal_formado_422_sin_codigos(cliente, sesion, cuerpo):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    ana = _turno_de_ana(cliente, datos, cabecera)

    respuesta = cliente.patch(f"/turnos/{ana['id']}", json=cuerpo, headers=cabecera)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []
    assert respuesta.json()["errores"][0]["campo"] is not None
    assert _horario_del_turno(cliente, ana["id"], cabecera) == ANA_13


def test_rep4b_un_id_que_no_es_entero_422_sin_codigos(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)

    respuesta = cliente.patch("/turnos/abc", json={"inicio": "2026-11-02T17:00:00Z"}, headers=cabecera)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []


def test_rep4b_el_404_va_antes_que_la_duracion(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)

    respuesta = cliente.patch("/turnos/999", json={"duracion_minutos": 42}, headers=cabecera)

    assert respuesta.status_code == 404
    assert respuesta.json()["codigos"] == ["RN-GL-04"]


@pytest.mark.parametrize("cuerpo", [{}, {"inicio": "2026-11-02T13:00:00Z", "duracion_minutos": 30}])
def test_rep4c_una_peticion_sin_cambios_200_y_el_historial_no_suma(cliente, sesion, cuerpo):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    ana = _turno_de_ana(cliente, datos, cabecera)
    un_bloqueo(sesion, datos["consultorio"], inicio=a_las(12), fin=a_las(15))  # creado después del turno (D83)

    respuesta = cliente.patch(f"/turnos/{ana['id']}", json=cuerpo, headers=cabecera)

    assert respuesta.status_code == 200
    assert (respuesta.json()["inicio"], respuesta.json()["fin"]) == (ANA_13[0], ANA_13[1])
    assert _tipos(cliente, ana["id"], cabecera) == ["creado"]


@pytest.mark.parametrize(
    "estado", ["cancelado_paciente", "cancelado_profesional", "vencido", "atendido", "ausente"]
)
def test_rep5a_un_turno_terminal_409_rn_ag_18_y_no_cambia(cliente, sesion, estado):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    terminal = _directo(sesion, datos, "ana", 13, estado=estado)

    respuesta = cliente.patch(f"/turnos/{terminal.id}", json={"inicio": "2026-11-02T19:00:00Z"}, headers=cabecera)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigos"] == ["RN-AG-18"]
    assert _horario_del_turno(cliente, terminal.id, cabecera) == (*ANA_13[:3], estado)


@pytest.mark.parametrize(
    ("estado", "hora"),
    [("pendiente_aprobacion", 14), ("pendiente_sena", 15), ("reservado", 16), ("confirmado", 17)],
)
def test_rep5a_un_turno_activo_se_mueve_y_conserva_su_estado(cliente, sesion, estado, hora):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    activo = _directo(sesion, datos, "bruno", hora, estado=estado)

    respuesta = cliente.patch(
        f"/turnos/{activo.id}", json={"inicio": f"2026-11-02T{hora}:30:00Z"}, headers=cabecera
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == estado
    assert respuesta.json()["inicio"] == f"2026-11-02T{hora}:30:00Z"


def test_rep5a_la_entrada_se_valida_antes_que_el_estado(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    terminal = _directo(sesion, datos, "ana", 13, estado="cancelado_paciente")

    respuesta = cliente.patch(f"/turnos/{terminal.id}", json={"duracion_minutos": 42}, headers=cabecera)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == ["RN-AG-01"]


@pytest.mark.parametrize("cuerpo", [{}, {"inicio": "2026-11-02T13:00:00Z", "duracion_minutos": 30}])
def test_rep5b_un_terminal_sin_cambios_200_sin_evento(cliente, sesion, cuerpo):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    ana = _turno_de_ana(cliente, datos, cabecera)
    sesion.execute(update(TurnoModelo).where(TurnoModelo.id == ana["id"]).values(estado="atendido"))
    sesion.commit()

    respuesta = cliente.patch(f"/turnos/{ana['id']}", json=cuerpo, headers=cabecera)

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "atendido"
    assert _tipos(cliente, ana["id"], cabecera) == ["creado"]


def test_rep5b_un_terminal_con_un_cambio_409_rn_ag_18(cliente, sesion):
    datos = _escenario(sesion)
    cabecera = _cabecera(sesion, datos, RECEPCIONISTA)
    ana = _turno_de_ana(cliente, datos, cabecera)
    sesion.execute(update(TurnoModelo).where(TurnoModelo.id == ana["id"]).values(estado="atendido"))
    sesion.commit()

    respuesta = cliente.patch(f"/turnos/{ana['id']}", json={"inicio": "2026-11-02T17:00:00Z"}, headers=cabecera)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigos"] == ["RN-AG-18"]
