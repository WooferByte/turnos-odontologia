"""El guard de las rutas del panel y las rutas públicas (US-092 CA-3; design R14).

La lista de rutas públicas es **cerrada**: una ruta nueva que olvide la protección hace fallar esto.
"""
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.api.seguridad import usuario_actual
from app.main import crear_app
from tests.factories import CONTRASENA_DE_PRUEBA, un_consultorio, un_usuario

RUTAS_PUBLICAS = {("/auth/login", "POST"), ("/auth/refresh", "POST")}


def _dependencias(dependiente) -> set:
    llamadas = set()
    for sub in dependiente.dependencies:
        llamadas.add(sub.call)
        llamadas |= _dependencias(sub)
    return llamadas


def _rutas(engine) -> list[tuple[APIRoute, str]]:
    app = crear_app(engine)
    return [(r, m) for r in app.routes if isinstance(r, APIRoute) for m in sorted(r.methods)]


def test_us092_ca3_toda_ruta_fuera_de_la_lista_publica_exige_el_access_token(engine) -> None:
    sin_proteccion = [
        (metodo, ruta.path)
        for ruta, metodo in _rutas(engine)
        if (ruta.path, metodo) not in RUTAS_PUBLICAS and usuario_actual not in _dependencias(ruta.dependant)
    ]

    assert sin_proteccion == []


def test_us092_ca3_las_rutas_publicas_son_solo_login_y_refresh(engine) -> None:
    publicas = {
        (ruta.path, metodo)
        for ruta, metodo in _rutas(engine)
        if usuario_actual not in _dependencias(ruta.dependant)
    }

    assert publicas == RUTAS_PUBLICAS


def test_us092_ca3_login_y_refresh_responden_sin_cabecera(engine, sesion) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))
    cliente = TestClient(crear_app(engine))

    login = cliente.post("/auth/login", json={"email": usuario.email, "contrasena": CONTRASENA_DE_PRUEBA})
    refresh = cliente.post("/auth/refresh", json={"refresh_token": login.json()["refresh_token"]})

    assert (login.status_code, refresh.status_code) == (200, 200)
