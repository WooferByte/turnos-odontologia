"""Sillones y turnos de punta a punta por HTTP (US-004 CA-1, CA-2 y CA-3).

Los sillones nuevos se crean con ``POST /sillones`` y los turnos con ``POST /turnos``: lo que se
prueba es cómo el catálogo cambia lo que ``crear_turno`` (C-01) acepta. Sin dobles.
"""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_reloj
from app.infrastructure.db.modelos import TurnoModelo
from app.main import crear_app
from tests.conftest import reloj_fijo
from tests.factories import un_consultorio, un_paciente, un_profesional, una_prestacion, un_sillon

DIA = "2026-11-02"


@pytest.fixture
def cliente(engine) -> TestClient:
    app = crear_app(engine)
    app.dependency_overrides[get_reloj] = lambda: reloj_fijo
    return TestClient(app)


@pytest.fixture
def datos(sesion) -> dict:
    """Consultorio con un profesional, un paciente, una prestación de 30 minutos y «Sillón 1»."""
    consultorio = un_consultorio(sesion)
    return {
        "consultorio": consultorio,
        "paciente": un_paciente(sesion, consultorio),
        "profesional": un_profesional(sesion, consultorio),
        "prestacion": una_prestacion(sesion, consultorio, duracion_minutos=30),
        "sillon": un_sillon(sesion, consultorio, nombre="Sillón 1"),
    }


def _pedir_turno(cliente, datos, hora: str, *, sillon_id=None, profesional_id=None, **extra):
    """``POST /turnos``; sin ``sillon_id`` ni ``profesional_id`` se omiten (RN-AG-14)."""
    cuerpo = {
        "paciente_id": datos["paciente"].id,
        "prestacion_id": datos["prestacion"].id,
        "inicio": f"{DIA}T{hora}:00Z",
        **extra,
    }
    if sillon_id is not None:
        cuerpo["sillon_id"] = sillon_id
    if profesional_id is not None:
        cuerpo["profesional_id"] = profesional_id
    return cliente.post("/turnos", json=cuerpo)


def _alta_de_sillon(cliente, nombre: str = "Sillón 2") -> int:
    respuesta = cliente.post("/sillones", json={"nombre": nombre})
    assert respuesta.status_code == 201
    return respuesta.json()["id"]


def _desactivar(cliente, sillon_id: int) -> None:
    assert cliente.patch(f"/sillones/{sillon_id}", json={"activo": False}).status_code == 200


def test_ca3_un_sillon_desactivado_no_admite_turnos_nuevos(cliente, sesion, datos):
    segundo = _alta_de_sillon(cliente)
    existente = _pedir_turno(cliente, datos, "10:00", sillon_id=segundo)
    assert existente.status_code == 201
    _desactivar(cliente, segundo)

    rechazado = _pedir_turno(cliente, datos, "11:00", sillon_id=segundo)

    assert rechazado.status_code == 422
    assert rechazado.json()["codigos"] == ["RN-GL-04"]
    assert rechazado.json()["referencias"] == [
        {"recurso": "sillon", "recurso_id": segundo, "motivo": "inactivo"}
    ]
    turno = sesion.get(TurnoModelo, existente.json()["id"])
    assert (turno.estado, turno.sillon_id) == ("reservado", segundo)
    assert turno.inicio.replace(tzinfo=None) == datetime.fromisoformat(f"{DIA}T10:00:00")
    assert sesion.query(TurnoModelo).count() == 1


def test_ca3_reactivar_vuelve_a_admitir_turnos(cliente, datos):
    segundo = _alta_de_sillon(cliente)
    _desactivar(cliente, segundo)
    reactivado = cliente.patch(f"/sillones/{segundo}", json={"activo": True})

    respuesta = _pedir_turno(cliente, datos, "11:00", sillon_id=segundo)

    assert reactivado.status_code == 200
    assert respuesta.status_code == 201
    assert respuesta.json()["sillon_id"] == segundo


def test_ca3_el_sillon_inactivo_se_informa_junto_con_otra_referencia(cliente, datos):
    segundo = _alta_de_sillon(cliente)
    _desactivar(cliente, segundo)
    peticion = {
        "paciente_id": datos["paciente"].id,
        "prestacion_id": 999,
        "inicio": f"{DIA}T11:00:00Z",
        "sillon_id": segundo,
    }

    respuesta = cliente.post("/turnos", json=peticion)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == ["RN-GL-04"]
    assert respuesta.json()["referencias"] == [
        {"recurso": "prestacion", "recurso_id": 999, "motivo": "inexistente"},
        {"recurso": "sillon", "recurso_id": segundo, "motivo": "inactivo"},
    ]


def test_ca1_con_un_unico_sillon_activo_el_turno_sin_sillon_va_a_ese(cliente, datos):
    respuesta = _pedir_turno(cliente, datos, "10:00")

    assert respuesta.status_code == 201
    assert respuesta.json()["sillon_id"] == datos["sillon"].id


def test_ca1_con_dos_sillones_activos_omitirlo_responde_varios_activos(cliente, sesion, datos):
    segundo = _alta_de_sillon(cliente)

    omitido = _pedir_turno(cliente, datos, "10:00")
    elegido = _pedir_turno(cliente, datos, "10:00", sillon_id=segundo)

    assert omitido.status_code == 422
    assert omitido.json()["codigos"] == ["RN-GL-04"]
    assert omitido.json()["referencias"] == [
        {"recurso": "sillon", "recurso_id": None, "motivo": "varios_activos"}
    ]
    assert elegido.status_code == 201
    assert elegido.json()["sillon_id"] == segundo
    assert sesion.query(TurnoModelo).count() == 1  # el rechazado no creó turno


def test_ca1_el_por_defecto_no_es_un_id_fijo(cliente, datos):
    segundo = _alta_de_sillon(cliente)
    _desactivar(cliente, datos["sillon"].id)

    respuesta = _pedir_turno(cliente, datos, "10:00")

    assert respuesta.status_code == 201
    assert respuesta.json()["sillon_id"] == segundo


def test_ca1_sin_sillones_activos_responde_ninguno_activo(cliente, datos):
    _desactivar(cliente, datos["sillon"].id)

    respuesta = _pedir_turno(cliente, datos, "10:00")

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == ["RN-GL-04"]
    assert respuesta.json()["referencias"] == [
        {"recurso": "sillon", "recurso_id": None, "motivo": "ninguno_activo"}
    ]
