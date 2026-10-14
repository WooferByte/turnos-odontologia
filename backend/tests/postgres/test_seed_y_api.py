"""Perfil opcional con PostgreSQL: el seed y la API sobre la base migrada (design I12, I13).

Sin mocks: sesiones, aplicación y base reales. El esquema sale de las migraciones (I9).
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.infrastructure.db.modelos import PacienteModelo
from app.infrastructure.db.seed_demo import ajustar_secuencias, cargar_demo_si_falta
from app.main import crear_app_desde_entorno

pytestmark = pytest.mark.postgres

PETICION_DE_EJEMPLO = {"paciente_id": 1, "prestacion_id": 1, "inicio": "2026-11-02T13:00:00Z"}


def test_despues_del_seed_se_puede_crear_un_paciente_sin_id(sesion: Session):
    assert cargar_demo_si_falta(sesion) is True
    ajustar_secuencias(sesion)

    nuevo = PacienteModelo(
        consultorio_id=1, nombre="Diego", apellido="Imaginario", telefono_whatsapp="+5491155550104"
    )
    sesion.add(nuevo)
    sesion.commit()

    # El seed fijó los identificadores 1 a 3: sin ajustar la secuencia el alta chocaría con el 1.
    assert nuevo.id == 4


def test_la_peticion_de_ejemplo_del_readme_responde_201_sobre_postgresql(
    engine: Engine, sesion: Session
):
    cargar_demo_si_falta(sesion)
    ajustar_secuencias(sesion)
    url = engine.url.render_as_string(hide_password=False)
    app = crear_app_desde_entorno({"DATABASE_URL": url})
    cliente = TestClient(app)

    primera = cliente.post("/turnos", json=PETICION_DE_EJEMPLO)
    repetida = cliente.post("/turnos", json=PETICION_DE_EJEMPLO)

    assert primera.status_code == 201
    assert primera.json()["profesional_id"] == 1
    assert primera.json()["sillon_id"] == 1
    assert repetida.status_code == 409
    assert repetida.json()["codigos"] == ["RN-AG-05", "RN-AG-08"]


def test_ca2_el_alta_de_un_sillon_tras_el_seed_no_choca_con_el_id_fijo(
    engine: Engine, sesion: Session
):
    cargar_demo_si_falta(sesion)
    ajustar_secuencias(sesion)
    url = engine.url.render_as_string(hide_password=False)
    cliente = TestClient(crear_app_desde_entorno({"DATABASE_URL": url}))

    alta = cliente.post("/sillones", json={"nombre": "Sillón 2"})
    listado = cliente.get("/sillones")

    assert alta.status_code == 201
    assert alta.json()["id"] != 1  # el seed fijó el id 1: sin ajustar la secuencia chocaría
    assert [(s["id"], s["nombre"], s["activo"]) for s in listado.json()] == [
        (1, "Sillón 1", True),
        (alta.json()["id"], "Sillón 2", True),
    ]
