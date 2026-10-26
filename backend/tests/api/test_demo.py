"""La demo de Swagger (D3, D19, D124): ``crear_app_demo()`` con el seed de datos ficticios.

Sin dobles: la aplicación, la base en memoria y el seed son los reales. Estos tests no usan el
``engine`` ni las factories de ``conftest.py``: la demo arma su propia base.
"""
import threading
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.db.seed_demo import CONTRASENA_DEMO, EMAIL_DEMO, EMAIL_RECEPCION_DEMO
from app.main import crear_app_demo

PETICION_DE_EJEMPLO = {"paciente_id": 1, "prestacion_id": 1, "inicio": "2026-11-02T13:00:00Z"}


def _cliente_con_sesion(email: str = EMAIL_DEMO) -> TestClient:
    """La demo con el usuario del seed ya autenticado: ``POST /auth/login`` y su access token (D211)."""
    cliente = TestClient(crear_app_demo())
    login = cliente.post("/auth/login", json={"email": email, "contrasena": CONTRASENA_DEMO})
    cliente.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
    return cliente


def _fecha(texto: str) -> datetime:
    return datetime.fromisoformat(texto)


def test_la_peticion_de_ejemplo_del_readme_responde_201():
    cliente = _cliente_con_sesion()

    primera = cliente.post("/turnos", json=PETICION_DE_EJEMPLO)
    repetida = cliente.post("/turnos", json=PETICION_DE_EJEMPLO)

    # Paso 1 del recorrido: 201 con el único profesional y el único sillón (RN-AG-14).
    assert primera.status_code == 201
    turno = primera.json()
    assert turno["id"] == 1
    assert turno["consultorio_id"] == 1
    assert turno["paciente_id"] == 1
    assert turno["profesional_id"] == 1
    assert turno["sillon_id"] == 1
    assert turno["prestacion_id"] == 1
    assert turno["duracion_minutos"] == 30
    assert turno["estado"] == "reservado"
    assert _fecha(turno["inicio"]) == _fecha("2026-11-02T13:00:00+00:00")
    assert _fecha(turno["fin"]) == _fecha("2026-11-02T13:30:00+00:00")
    # Paso 2: repetirla choca con el profesional y con el sillón (E4).
    assert repetida.status_code == 409
    assert repetida.json()["codigos"] == ["RN-AG-05", "RN-AG-08"]


def test_la_peticion_de_ejemplo_con_una_prestacion_inexistente_responde_422_con_rn_gl_04():
    cliente = _cliente_con_sesion()

    respuesta = cliente.post("/turnos", json={**PETICION_DE_EJEMPLO, "prestacion_id": 999})

    # Paso 3 del recorrido de la prueba manual.
    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-GL-04"]
    assert cuerpo["referencias"] == [
        {"recurso": "prestacion", "recurso_id": 999, "motivo": "inexistente"}
    ]


@pytest.mark.parametrize(
    ("prestacion_id", "duracion_minutos"),
    [(1, 30), (2, 45), (3, 60), (4, 45), (5, 30)],
)
def test_el_seed_de_la_demo_deja_las_cinco_prestaciones_con_su_duracion(
    prestacion_id, duracion_minutos
):
    cliente = _cliente_con_sesion()

    respuesta = cliente.post(
        "/turnos", json={**PETICION_DE_EJEMPLO, "prestacion_id": prestacion_id}
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["duracion_minutos"] == duracion_minutos


@pytest.mark.parametrize("paciente_id", [1, 2, 3])
def test_el_seed_de_la_demo_deja_tres_pacientes_y_ninguno_mas(paciente_id):
    cliente = _cliente_con_sesion()

    existente = cliente.post("/turnos", json={**PETICION_DE_EJEMPLO, "paciente_id": paciente_id})
    inexistente = cliente.post("/turnos", json={**PETICION_DE_EJEMPLO, "paciente_id": 4})

    assert existente.status_code == 201
    assert inexistente.status_code == 422
    assert inexistente.json()["referencias"] == [
        {"recurso": "paciente", "recurso_id": 4, "motivo": "inexistente"}
    ]


def test_la_demo_lista_las_cinco_prestaciones_con_su_color():
    cliente = _cliente_con_sesion()

    respuesta = cliente.get("/prestaciones")

    assert respuesta.status_code == 200
    assert [(p["id"], p["nombre"], p["color"]) for p in respuesta.json()] == [
        (1, "Consulta / control", "#1E88E5"),
        (2, "Limpieza", "#43A047"),
        (3, "Obturación", "#FB8C00"),
        (4, "Extracción", "#E53935"),
        (5, "Urgencia", "#8E24AA"),
    ]


def test_us090_ca1_la_demo_inicia_sesion_con_el_usuario_del_seed():
    cliente = TestClient(crear_app_demo())

    correcta = cliente.post(
        "/auth/login",
        json={"email": "odontologa@consultorio-demo.test", "contrasena": CONTRASENA_DEMO},
    )
    incorrecta = cliente.post(
        "/auth/login",
        json={"email": "odontologa@consultorio-demo.test", "contrasena": "otra-contrasena-ficticia"},
    )

    assert correcta.status_code == 200
    assert set(correcta.json()) >= {"access_token", "refresh_token", "token_type", "expires_in"}
    assert incorrecta.status_code == 401


def test_us092_ca1_la_demo_sin_token_responde_401():
    cliente = TestClient(crear_app_demo())

    respuesta = cliente.post("/turnos", json=PETICION_DE_EJEMPLO)

    assert respuesta.status_code == 401
    assert respuesta.json()["codigos"] == ["RN-AU-03"]


def test_us091_ca3_la_recepcionista_de_la_demo_recibe_403_en_prestaciones():
    cliente = _cliente_con_sesion(EMAIL_RECEPCION_DEMO)

    prestacion = cliente.post("/prestaciones", json={"nombre": "Blanqueamiento", "duracion_minutos": 30})
    turno = cliente.post("/turnos", json=PETICION_DE_EJEMPLO)

    assert prestacion.status_code == 403
    assert prestacion.json()["codigos"] == ["RN-AU-05"]
    assert turno.status_code == 201


def test_us002_ca1_la_demo_arranca_con_el_horario_de_ejemplo_y_el_turno_de_las_08_es_rechazado():
    cliente = _cliente_con_sesion()

    horario = cliente.get("/profesionales/1/horario")
    dentro = cliente.post("/turnos", json=PETICION_DE_EJEMPLO)  # 13:00Z = lunes 10:00 del consultorio
    fuera = cliente.post("/turnos", json={**PETICION_DE_EJEMPLO, "inicio": "2026-11-02T11:00:00Z"})  # 08:00 local

    assert horario.status_code == 200
    assert horario.json()["franjas"] == [
        {"dia_semana": dia, "hora_inicio": desde, "hora_fin": hasta}
        for dia in range(5)
        for desde, hasta in (("09:00", "13:00"), ("15:00", "19:00"))
    ]
    assert dentro.status_code == 201
    assert fuera.status_code == 422
    assert fuera.json()["codigos"] == ["RN-AG-04"]


@pytest.mark.parametrize("rondas", [1, 5])
def test_la_demo_responde_peticiones_en_paralelo_sin_romper_la_base_compartida(rondas):
    # La base en memoria de la demo es una sola conexión de SQLite (StaticPool): sin el candado,
    # los hilos del threadpool la usan a la vez y fallan con InterfaceError o se traban.
    rutas = ["/prestaciones", "/profesionales", "/bloqueos", "/usuarios", "/sillones"] * 3
    with _cliente_con_sesion() as cliente:
        estados: list[int | str] = []

        def pedir(ruta: str) -> None:
            try:
                estados.append(cliente.get(ruta).status_code)
            except Exception as error:  # el error de la base es el resultado a comparar
                estados.append(type(error).__name__)

        for _ in range(rondas):
            # Hilos daemon: si la base se traba, el test falla por tiempo sin colgar la suite.
            hilos = [threading.Thread(target=pedir, args=(ruta,), daemon=True) for ruta in rutas]
            for hilo in hilos:
                hilo.start()
            for hilo in hilos:
                hilo.join(timeout=10)

        assert estados == [200] * len(rutas) * rondas
