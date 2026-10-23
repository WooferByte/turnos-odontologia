"""Perfil opcional con PostgreSQL: el seed y la API sobre la base migrada (design I12, I13).

Sin mocks: sesiones, aplicación y base reales. El esquema sale de las migraciones (I9).
"""
from datetime import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, delete, func, select
from sqlalchemy.orm import Session

from app.infrastructure.db import cargar_seed
from app.domain.acceso.roles import Rol
from app.infrastructure.db.modelos import (
    ConsultorioModelo,
    FranjaHorariaModelo,
    PacienteModelo,
    ProfesionalModelo,
    UsuarioModelo,
    UsuarioRolModelo,
)
from app.infrastructure.db.seed_demo import (
    CONTRASENA_DEMO,
    EMAIL_DEMO,
    EMAIL_RECEPCION_DEMO,
    ajustar_secuencias,
    cargar_demo_si_falta,
    cargar_usuario_demo_si_falta,
)
from app.infrastructure.seguridad.contrasenas import HasherBcrypt
from app.main import crear_app_desde_entorno
from tests.conftest import SECRETO_DE_PRUEBA

pytestmark = pytest.mark.postgres

PETICION_DE_EJEMPLO = {"paciente_id": 1, "prestacion_id": 1, "inicio": "2026-11-02T13:00:00Z"}


def _cliente_con_sesion(engine: Engine, email: str = EMAIL_DEMO) -> TestClient:
    """Siembra como el contenedor, inicia sesión por HTTP y deja el access token en el cliente (R16, D211)."""
    url = engine.url.render_as_string(hide_password=False)
    cargar_seed.main({"DATABASE_URL": url, "SEED_USUARIO_PASSWORD": CONTRASENA_DEMO})
    cliente = TestClient(crear_app_desde_entorno({"DATABASE_URL": url, "JWT_SECRET": SECRETO_DE_PRUEBA}))
    login = cliente.post("/auth/login", json={"email": email, "contrasena": CONTRASENA_DEMO})
    assert login.status_code == 200
    cliente.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
    return cliente


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


def test_la_peticion_de_ejemplo_del_readme_responde_201_sobre_postgresql(engine: Engine):
    cliente = _cliente_con_sesion(engine)

    primera = cliente.post("/turnos", json=PETICION_DE_EJEMPLO)
    repetida = cliente.post("/turnos", json=PETICION_DE_EJEMPLO)

    assert primera.status_code == 201
    assert primera.json()["profesional_id"] == 1
    assert primera.json()["sillon_id"] == 1
    assert repetida.status_code == 409
    assert repetida.json()["codigos"] == ["RN-AG-05", "RN-AG-08"]


def test_ca2_el_alta_de_un_sillon_tras_el_seed_no_choca_con_el_id_fijo(engine: Engine):
    cliente = _cliente_con_sesion(engine)

    alta = cliente.post("/sillones", json={"nombre": "Sillón 2"})
    listado = cliente.get("/sillones")

    assert alta.status_code == 201
    assert alta.json()["id"] != 1  # el seed fijó el id 1: sin ajustar la secuencia chocaría
    assert [(s["id"], s["nombre"], s["activo"]) for s in listado.json()] == [
        (1, "Sillón 1", True),
        (alta.json()["id"], "Sillón 2", True),
    ]


def test_us090_ca4_volumen_sembrado_sin_usuario_recibe_el_usuario(sesion: Session):
    # Volumen anterior a C-06: el consultorio 1 ya está sembrado y no hay ningún usuario.
    assert cargar_demo_si_falta(sesion) is True
    ajustar_secuencias(sesion)
    assert sesion.scalar(select(func.count()).select_from(UsuarioModelo)) == 0

    cargado = cargar_usuario_demo_si_falta(sesion, HasherBcrypt(rondas=4).hashear(CONTRASENA_DEMO))
    repetido = cargar_usuario_demo_si_falta(sesion, HasherBcrypt(rondas=4).hashear(CONTRASENA_DEMO))
    ajustar_secuencias(sesion)

    assert (cargado, repetido) == (True, False)
    assert sesion.scalar(select(func.count()).select_from(UsuarioModelo)) == 1
    assert sesion.scalar(select(func.count()).select_from(ConsultorioModelo)) == 1
    otro = UsuarioModelo(
        consultorio_id=1,
        email="otra@consultorio-demo.test",
        hash_password="hash-ficticio",
        activo=True,
        token_version=0,
        creado_en=sesion.scalar(select(UsuarioModelo.creado_en)),
    )
    sesion.add(otro)
    sesion.commit()
    # El seed fijó el id 1: con la secuencia sin avanzar, el alta sin id chocaría.
    assert otro.id == 2


def test_us090_ca1_inicio_de_sesion_sobre_postgresql(engine: Engine, sesion: Session):
    url = engine.url.render_as_string(hide_password=False)
    cargar_seed.main({"DATABASE_URL": url, "SEED_USUARIO_PASSWORD": CONTRASENA_DEMO})
    cliente = TestClient(crear_app_desde_entorno({"DATABASE_URL": url, "JWT_SECRET": SECRETO_DE_PRUEBA}))

    correcta = cliente.post("/auth/login", json={"email": EMAIL_DEMO, "contrasena": CONTRASENA_DEMO})
    incorrecta = cliente.post(
        "/auth/login", json={"email": EMAIL_DEMO, "contrasena": "otra-contrasena-ficticia"}
    )

    assert correcta.status_code == 200
    assert set(correcta.json()) >= {"access_token", "refresh_token", "token_type", "expires_in"}
    assert incorrecta.status_code == 401


def test_us092_ca1_el_recorrido_sin_token_responde_401_sobre_postgresql(engine: Engine):
    url = engine.url.render_as_string(hide_password=False)
    cargar_seed.main({"DATABASE_URL": url, "SEED_USUARIO_PASSWORD": CONTRASENA_DEMO})
    cliente = TestClient(crear_app_desde_entorno({"DATABASE_URL": url, "JWT_SECRET": SECRETO_DE_PRUEBA}))

    sin_token = cliente.post("/turnos", json=PETICION_DE_EJEMPLO)

    assert sin_token.status_code == 401
    assert sin_token.json()["codigos"] == ["RN-AU-03"]


def test_us091_ca3_la_recepcionista_recibe_403_en_prestaciones_y_201_en_turnos(engine: Engine):
    cliente = _cliente_con_sesion(engine, EMAIL_RECEPCION_DEMO)

    alta = cliente.post("/prestaciones", json={"nombre": "Prestación nueva", "duracion_minutos": 30})
    turno = cliente.post("/turnos", json=PETICION_DE_EJEMPLO)

    assert alta.status_code == 403
    assert alta.json()["codigos"] == ["RN-AU-05"]
    assert turno.status_code == 201


def test_us091_ca4_volumen_sembrado_en_c06_recibe_roles_y_vinculo(engine: Engine, sesion: Session):
    # Volumen del autor tras C-06: consultorio y usuario sembrados, sin roles ni vínculo.
    cargar_demo_si_falta(sesion)
    cargar_usuario_demo_si_falta(sesion, HasherBcrypt(rondas=4).hashear(CONTRASENA_DEMO))
    ajustar_secuencias(sesion)
    assert sesion.scalar(select(func.count()).select_from(UsuarioRolModelo)) == 0
    assert sesion.get(ProfesionalModelo, 1).usuario_id is None
    url = engine.url.render_as_string(hide_password=False)
    entorno = {"DATABASE_URL": url, "SEED_USUARIO_PASSWORD": CONTRASENA_DEMO}

    cargar_seed.main(entorno)
    cargar_seed.main(entorno)  # repetir no duplica nada
    sesion.expire_all()

    roles = {(r.usuario_id, r.rol) for r in sesion.scalars(select(UsuarioRolModelo))}
    assert roles == {(1, Rol.ODONTOLOGO.value), (1, Rol.DUENO.value), (2, Rol.RECEPCIONISTA.value)}
    assert sesion.get(ProfesionalModelo, 1).usuario_id == 1
    assert sesion.scalar(select(func.count()).select_from(UsuarioModelo)) == 2
    assert sesion.scalar(select(func.count()).select_from(ConsultorioModelo)) == 1
    # La secuencia de usuario avanzó: un alta sin id no choca con los ids 1 y 2.
    otro = UsuarioModelo(
        consultorio_id=1,
        email="otra@consultorio-demo.test",
        hash_password="hash-ficticio",
        activo=True,
        token_version=0,
        creado_en=sesion.scalar(select(UsuarioModelo.creado_en)),
    )
    sesion.add(otro)
    sesion.commit()
    assert otro.id == 3


def test_us002_ca1_volver_a_cargar_la_demo_no_duplica_el_horario(engine: Engine, sesion: Session):
    url = engine.url.render_as_string(hide_password=False)
    entorno = {"DATABASE_URL": url, "SEED_USUARIO_PASSWORD": CONTRASENA_DEMO}

    cargar_seed.main(entorno)
    cargar_seed.main(entorno)  # repetir no duplica nada
    sesion.expire_all()

    franjas = sesion.execute(
        select(FranjaHorariaModelo.dia_semana, FranjaHorariaModelo.hora_inicio, FranjaHorariaModelo.hora_fin)
        .where(FranjaHorariaModelo.profesional_id == 1)
        .order_by(FranjaHorariaModelo.dia_semana, FranjaHorariaModelo.hora_inicio)
    ).all()
    assert [tuple(f) for f in franjas] == [
        (dia, time(desde), time(hasta)) for dia in range(5) for desde, hasta in ((9, 13), (15, 19))
    ]


def test_us002_ca1_volumen_sembrado_antes_de_c12_recibe_el_horario(engine: Engine, sesion: Session):
    # Volumen del autor tras C-11: el profesional 1 existe y la tabla franja_horaria esta vacia.
    cargar_demo_si_falta(sesion)
    sesion.execute(delete(FranjaHorariaModelo))
    sesion.commit()
    url = engine.url.render_as_string(hide_password=False)

    cargar_seed.main({"DATABASE_URL": url, "SEED_USUARIO_PASSWORD": CONTRASENA_DEMO})
    sesion.expire_all()

    assert sesion.scalar(select(func.count()).select_from(FranjaHorariaModelo)) == 10
