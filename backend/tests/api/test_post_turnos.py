"""``POST /turnos`` por HTTP con ``TestClient`` sobre ``crear_app(engine)`` (D3, D4, D12, D16).

Sin dobles: la sesión y el repositorio son los reales, sobre el engine SQLite del test. Solo se
sustituye el reloj, con ``app.dependency_overrides[get_reloj]``.
"""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_reloj
from app.main import crear_app
from tests.conftest import RELOJ_FIJO, a_las, reloj_fijo
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
)

CAMPOS_DE_TURNO_SALIDA = {
    "id",
    "consultorio_id",
    "paciente_id",
    "profesional_id",
    "sillon_id",
    "prestacion_id",
    "inicio",
    "fin",
    "duracion_minutos",
    "estado",
    "creado_en",
}


@pytest.fixture
def cliente(engine) -> TestClient:
    app = crear_app(engine)
    app.dependency_overrides[get_reloj] = lambda: reloj_fijo
    return TestClient(app)


def _escenario(sesion, duracion_minutos: int = 30) -> dict:
    consultorio = un_consultorio(sesion)
    return {
        "consultorio": consultorio,
        "paciente": un_paciente(sesion, consultorio),
        "profesional": un_profesional(sesion, consultorio),
        "sillon": un_sillon(sesion, consultorio),
        "prestacion": una_prestacion(sesion, consultorio, duracion_minutos=duracion_minutos),
    }


def _fecha(texto: str) -> datetime:
    return datetime.fromisoformat(texto)


def test_e1_post_turnos_responde_201(cliente, sesion):
    datos = _escenario(sesion, duracion_minutos=30)

    respuesta = cliente.post(
        "/turnos",
        json={
            "paciente_id": datos["paciente"].id,
            "prestacion_id": datos["prestacion"].id,
            "inicio": "2026-11-02T10:00:00Z",
            "profesional_id": datos["profesional"].id,
            "sillon_id": datos["sillon"].id,
        },
    )

    assert respuesta.status_code == 201
    assert respuesta.headers["content-type"] == "application/json"
    cuerpo = respuesta.json()
    assert set(cuerpo) == CAMPOS_DE_TURNO_SALIDA
    assert isinstance(cuerpo["id"], int)
    assert cuerpo["consultorio_id"] == datos["consultorio"].id
    assert cuerpo["paciente_id"] == datos["paciente"].id
    assert cuerpo["profesional_id"] == datos["profesional"].id
    assert cuerpo["sillon_id"] == datos["sillon"].id
    assert cuerpo["prestacion_id"] == datos["prestacion"].id
    assert _fecha(cuerpo["inicio"]) == a_las(10)
    assert _fecha(cuerpo["fin"]) == a_las(10, 30)
    assert cuerpo["duracion_minutos"] == 30
    assert cuerpo["estado"] == "reservado"
    assert _fecha(cuerpo["creado_en"]) == RELOJ_FIJO
    assert _fecha(cuerpo["inicio"]).utcoffset() == timedelta(0)


def _peticion(datos: dict, inicio: str, **extra) -> dict:
    return {
        "paciente_id": datos["paciente"].id,
        "prestacion_id": datos["prestacion"].id,
        "inicio": inicio,
        "profesional_id": datos["profesional"].id,
        "sillon_id": datos["sillon"].id,
        **extra,
    }


def test_e4_post_turnos_responde_409_con_los_dos_codigos(cliente, sesion):
    datos = _escenario(sesion)
    existente = un_turno(
        sesion,
        paciente=datos["paciente"],
        profesional=datos["profesional"],
        sillon=datos["sillon"],
        prestacion=datos["prestacion"],
        inicio=a_las(10),
    )

    respuesta = cliente.post("/turnos", json=_peticion(datos, "2026-11-02T10:00:00Z"))

    assert respuesta.status_code == 409
    assert respuesta.headers["content-type"] == "application/problem+json"
    assert respuesta.json() == {
        "type": "/errores/solapamiento-turno",
        "title": "Turno solapado",
        "status": 409,
        "detail": "El profesional y el sillón ya tienen un turno activo en ese horario.",
        "instance": "/turnos",
        "codigos": ["RN-AG-05", "RN-AG-08"],
        "conflictos": [
            {
                "codigo": "RN-AG-05",
                "recurso": "profesional",
                "recurso_id": datos["profesional"].id,
                "turno_id": existente.id,
            },
            {
                "codigo": "RN-AG-08",
                "recurso": "sillon",
                "recurso_id": datos["sillon"].id,
                "turno_id": existente.id,
            },
        ],
    }


def test_e12_post_turnos_responde_422_con_rn_gl_04(cliente, sesion):
    datos = _escenario(sesion)
    sillon_inactivo = un_sillon(sesion, datos["consultorio"], activo=False)

    respuesta = cliente.post(
        "/turnos",
        json=_peticion(
            datos, "2026-11-02T10:00:00Z", prestacion_id=999, sillon_id=sillon_inactivo.id
        ),
    )

    assert respuesta.status_code == 422
    assert respuesta.headers["content-type"] == "application/problem+json"
    assert respuesta.json() == {
        "type": "/errores/entrada-invalida",
        "title": "Entrada inválida",
        "status": 422,
        "detail": (
            "La petición tiene 2 problemas de entrada: prestacion 999 (inexistente); "
            f"sillon {sillon_inactivo.id} (inactivo)."
        ),
        "instance": "/turnos",
        "codigos": ["RN-GL-04"],
        "referencias": [
            {"recurso": "prestacion", "recurso_id": 999, "motivo": "inexistente"},
            {"recurso": "sillon", "recurso_id": sillon_inactivo.id, "motivo": "inactivo"},
        ],
        "errores": [],
    }


MENSAJE_FECHA_NO_UTC = (
    "La fecha y hora debe tener zona y estar en UTC, por ejemplo 2026-11-02T13:00:00Z."
)


@pytest.mark.parametrize(
    "inicio",
    ["2026-11-02T10:00:00", "2026-11-02T10:00:00-03:00"],
    ids=["sin_zona", "desfase_menos_tres"],
)
def test_fecha_sin_zona_responde_422_con_rn_gl_01(cliente, sesion, inicio):
    datos = _escenario(sesion)

    respuesta = cliente.post("/turnos", json=_peticion(datos, inicio))

    assert respuesta.status_code == 422
    assert respuesta.headers["content-type"] == "application/problem+json"
    assert respuesta.json() == {
        "type": "/errores/entrada-invalida",
        "title": "Entrada inválida",
        "status": 422,
        "detail": "La petición tiene 1 problema de entrada: inicio debe tener zona y estar en UTC.",
        "instance": "/turnos",
        "codigos": ["RN-GL-01"],
        "referencias": [],
        "errores": [{"campo": "inicio", "codigo": "RN-GL-01", "mensaje": MENSAJE_FECHA_NO_UTC}],
    }


def test_fecha_sin_zona_y_referencia_invalida_responde_un_422_con_los_dos_codigos(cliente, sesion):
    datos = _escenario(sesion)

    respuesta = cliente.post(
        "/turnos", json=_peticion(datos, "2026-11-02T10:00:00", prestacion_id=999)
    )

    assert respuesta.status_code == 422
    assert respuesta.headers["content-type"] == "application/problem+json"
    assert respuesta.json() == {
        "type": "/errores/entrada-invalida",
        "title": "Entrada inválida",
        "status": 422,
        "detail": (
            "La petición tiene 2 problemas de entrada: inicio debe tener zona y estar en UTC; "
            "prestacion 999 (inexistente)."
        ),
        "instance": "/turnos",
        "codigos": ["RN-GL-01", "RN-GL-04"],
        "referencias": [{"recurso": "prestacion", "recurso_id": 999, "motivo": "inexistente"}],
        "errores": [{"campo": "inicio", "codigo": "RN-GL-01", "mensaje": MENSAJE_FECHA_NO_UTC}],
    }


def test_cruce_de_medianoche_responde_422_con_rn_ag_10d(cliente, sesion):
    datos = _escenario(sesion, duracion_minutos=30)

    # 02:45 UTC con 30 minutos: de 23:45 a 00:15 en Buenos Aires.
    respuesta = cliente.post("/turnos", json=_peticion(datos, "2026-11-03T02:45:00Z"))

    assert respuesta.status_code == 422
    assert respuesta.headers["content-type"] == "application/problem+json"
    assert respuesta.json() == {
        "type": "/errores/intervalo-invalido",
        "title": "Intervalo inválido",
        "status": 422,
        "detail": "El turno no puede cruzar la medianoche del consultorio.",
        "instance": "/turnos",
        "codigos": ["RN-AG-10d"],
    }


def test_cuerpo_invalido_responde_problem_json(cliente, sesion):
    datos = _escenario(sesion)
    peticion = _peticion(datos, "2026-11-02T10:00:00Z", duracion_minutos=45)
    del peticion["inicio"]  # falta inicio y sobra duracion_minutos

    respuesta = cliente.post("/turnos", json=peticion)

    assert respuesta.status_code == 422
    assert respuesta.headers["content-type"] == "application/problem+json"
    assert respuesta.json() == {
        "type": "/errores/entrada-invalida",
        "title": "Entrada inválida",
        "status": 422,
        "detail": (
            "La petición tiene 2 problemas de entrada: el cuerpo no tiene el formato esperado."
        ),
        "instance": "/turnos",
        "codigos": [],
        "referencias": [],
        "errores": [
            {"campo": "inicio", "codigo": None, "mensaje": "Field required"},
            {"campo": "duracion_minutos", "codigo": None, "mensaje": "Extra inputs are not permitted"},
        ],
    }


def test_cuerpo_con_json_roto_responde_problem_json_sin_campo(cliente):
    respuesta = cliente.post(
        "/turnos", content="{esto no es json", headers={"Content-Type": "application/json"}
    )

    assert respuesta.status_code == 422
    assert respuesta.headers["content-type"] == "application/problem+json"
    assert respuesta.json() == {
        "type": "/errores/entrada-invalida",
        "title": "Entrada inválida",
        "status": 422,
        "detail": (
            "La petición tiene 1 problema de entrada: el cuerpo no tiene el formato esperado."
        ),
        "instance": "/turnos",
        "codigos": [],
        "referencias": [],
        "errores": [{"campo": None, "codigo": None, "mensaje": "JSON decode error"}],
    }


def test_sillon_omitido_con_varios_activos_responde_422_sin_id_en_el_detalle(cliente, sesion):
    datos = _escenario(sesion)
    un_sillon(sesion, datos["consultorio"])  # ahora hay dos sillones activos (RN-AG-14)
    peticion = _peticion(datos, "2026-11-02T10:00:00Z")
    del peticion["sillon_id"]

    respuesta = cliente.post("/turnos", json=peticion)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == ["RN-GL-04"]
    assert respuesta.json()["referencias"] == [
        {"recurso": "sillon", "recurso_id": None, "motivo": "varios_activos"}
    ]
    assert respuesta.json()["detail"] == (
        "La petición tiene 1 problema de entrada: sillon (varios_activos)."
    )
