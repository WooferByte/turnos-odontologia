"""``/profesionales`` y su horario por HTTP con ``TestClient`` sobre ``crear_app(engine)`` (US-002 CA-1; HOR-1).

Sin dobles: la sesión y los repositorios son los reales, sobre el engine SQLite del test. Cada rol
manda un access token real (D211). Todos los datos son ficticios (RN-PR-01).
"""
from datetime import datetime, time, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_reloj
from app.domain.acceso.roles import Rol
from app.domain.agenda.horario import Franja
from app.infrastructure.configuracion import ConfiguracionDeSesion
from app.infrastructure.db.modelos import TurnoModelo
from app.infrastructure.repositories.horario import RepositorioHorarioSqlAlchemy
from app.main import crear_app
from tests.conftest import SECRETO_DE_PRUEBA, con_token_del_panel, reloj_fijo
from tests.factories import franja, un_consultorio, un_paciente, un_profesional, un_sillon, un_turno, una_prestacion

ZONA = "America/Argentina/Buenos_Aires"
PROBLEMA_JSON = "application/problem+json"


@pytest.fixture
def app(engine):
    app = crear_app(engine, ConfiguracionDeSesion(SECRETO_DE_PRUEBA, rondas_bcrypt=4))
    app.dependency_overrides[get_reloj] = lambda: reloj_fijo
    return app


def _cliente(app, engine, roles: tuple[Rol, ...]) -> TestClient:
    return con_token_del_panel(TestClient(app), engine, roles)


@pytest.fixture
def odontologa(app, engine) -> TestClient:
    return _cliente(app, engine, (Rol.ODONTOLOGO,))


@pytest.fixture
def recepcionista(app, engine) -> TestClient:
    return _cliente(app, engine, (Rol.RECEPCIONISTA,))


@pytest.fixture
def dueno(app, engine) -> TestClient:
    return _cliente(app, engine, (Rol.DUENO,))


def _f(dia, desde, hasta):
    """Franja del cuerpo de un ``PUT``."""
    return {"dia_semana": dia, "hora_inicio": desde, "hora_fin": hasta}


def _guardadas(fabrica_sesiones, profesional_id) -> list[Franja]:
    with fabrica_sesiones() as sesion:
        return list(RepositorioHorarioSqlAlchemy(sesion).franjas_de(profesional_id))


def test_us002_ca1_se_leen_las_franjas_de_manana_y_de_tarde(recepcionista, sesion):
    profesional = un_profesional(
        sesion,
        un_consultorio(sesion),
        horario=(franja(0, "15:00", "19:00"), franja(0, "09:00", "13:00")),
    )

    respuesta = recepcionista.get(f"/profesionales/{profesional.id}/horario")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "profesional_id": profesional.id,
        "zona_horaria": ZONA,
        "franjas": [_f(0, "09:00", "13:00"), _f(0, "15:00", "19:00")],
    }


def test_us002_ca1_la_odontologa_carga_manana_y_tarde(odontologa, sesion):
    profesional = un_profesional(sesion, un_consultorio(sesion), horario=())

    respuesta = odontologa.put(
        f"/profesionales/{profesional.id}/horario",
        json={"franjas": [_f(2, "15:00", "19:00"), _f(2, "09:00", "13:00")]},
    )

    esperado = [_f(2, "09:00", "13:00"), _f(2, "15:00", "19:00")]
    assert respuesta.status_code == 200
    assert respuesta.json() == {"profesional_id": profesional.id, "zona_horaria": ZONA, "franjas": esperado}
    assert odontologa.get(f"/profesionales/{profesional.id}/horario").json()["franjas"] == esperado


def test_hor1_dos_franjas_superpuestas_del_mismo_dia_se_rechazan(odontologa, sesion, fabrica_sesiones):
    profesional = un_profesional(sesion, un_consultorio(sesion), horario=(franja(0, "09:00", "13:00"),))

    respuesta = odontologa.put(
        f"/profesionales/{profesional.id}/horario",
        json={"franjas": [_f(2, "09:00", "13:00"), _f(2, "12:00", "16:00")]},
    )

    assert respuesta.status_code == 422
    assert respuesta.headers["content-type"] == PROBLEMA_JSON
    cuerpo = respuesta.json()
    assert cuerpo["codigos"] == ["RN-AG-16"]
    assert cuerpo["errores"] == [
        {
            "campo": "franjas.1",
            "codigo": "RN-AG-16",
            "mensaje": "franjas.1 se superpone con otra franja del mismo día",
        }
    ]
    assert _guardadas(fabrica_sesiones, profesional.id) == [Franja(0, time(9, 0), time(13, 0))]


def test_us002_ca1_mas_de_70_franjas_se_rechazan_como_formato(odontologa, sesion, fabrica_sesiones):
    profesional = un_profesional(sesion, un_consultorio(sesion), horario=(franja(0, "09:00", "13:00"),))
    setenta = [_f(dia, f"{hora:02d}:00", f"{hora + 1:02d}:00") for dia in range(7) for hora in range(8, 18)]
    setenta_y_una = [*setenta, _f(6, "18:00", "19:00")]
    assert (len(setenta), len(setenta_y_una)) == (70, 71)

    rechazo = odontologa.put(f"/profesionales/{profesional.id}/horario", json={"franjas": setenta_y_una})

    assert rechazo.status_code == 422
    assert rechazo.json()["codigos"] == []
    assert [e["campo"] for e in rechazo.json()["errores"]] == ["franjas"]
    assert _guardadas(fabrica_sesiones, profesional.id) == [Franja(0, time(9, 0), time(13, 0))]
    aceptado = odontologa.put(f"/profesionales/{profesional.id}/horario", json={"franjas": setenta})
    assert aceptado.status_code == 200
    assert len(aceptado.json()["franjas"]) == 70


def test_us002_ca1_la_recepcionista_lista_los_profesionales(recepcionista, sesion):
    consultorio = un_consultorio(sesion)
    primero = un_profesional(sesion, consultorio, nombre="Dra. Demo Ficticia")
    segundo = un_profesional(sesion, consultorio, nombre="Dr. Inactivo Ficticio", activo=False)

    respuesta = recepcionista.get("/profesionales")

    assert respuesta.status_code == 200
    assert respuesta.json() == [
        {"id": primero.id, "nombre": "Dra. Demo Ficticia", "activo": True},
        {"id": segundo.id, "nombre": "Dr. Inactivo Ficticio", "activo": False},
    ]


# --- US-002 CA-1 y HOR-1: bordes ------------------------------------------------------------------
MENSAJE_SUPERPUESTA = "franjas.{i} se superpone con otra franja del mismo día"
MENSAJE_INVERTIDA = "franjas.{i} debe terminar después de empezar"


def _errores(respuesta) -> list[tuple[str, str, str]]:
    return [(e["campo"], e["codigo"], e["mensaje"]) for e in respuesta.json()["errores"]]


def test_us002_ca1_un_profesional_sin_horario_responde_la_lista_vacia(dueno, sesion):
    profesional = un_profesional(sesion, un_consultorio(sesion), horario=())

    respuesta = dueno.get(f"/profesionales/{profesional.id}/horario")

    assert respuesta.status_code == 200
    assert respuesta.json()["franjas"] == []


def test_us002_ca1_un_profesional_inexistente_responde_404_con_rn_gl_04(odontologa, sesion):
    un_consultorio(sesion)

    respuesta = odontologa.get("/profesionales/999/horario")

    assert respuesta.status_code == 404
    assert respuesta.json()["codigos"] == ["RN-GL-04"]
    assert respuesta.json()["referencias"] == [
        {"recurso": "profesional", "recurso_id": 999, "motivo": "inexistente"}
    ]


def test_us002_ca1_un_id_que_no_es_entero_responde_422_de_formato_y_no_404(odontologa, sesion):
    un_consultorio(sesion)

    respuesta = odontologa.get("/profesionales/abc/horario")

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []
    assert [e["campo"] for e in respuesta.json()["errores"]] == ["profesional_id"]


@pytest.mark.parametrize(
    "franjas",
    [
        [_f(0, "09:00", "13:00"), _f(0, "13:00", "17:00")],  # contiguas
        [_f(0, "09:00", "13:00"), _f(1, "09:00", "13:00")],  # mismo horario en días distintos
    ],
)
def test_us002_ca1_franjas_contiguas_y_el_mismo_horario_en_dias_distintos_se_aceptan(odontologa, sesion, franjas):
    profesional = un_profesional(sesion, un_consultorio(sesion), horario=())

    respuesta = odontologa.put(f"/profesionales/{profesional.id}/horario", json={"franjas": franjas})

    assert respuesta.status_code == 200
    assert respuesta.json()["franjas"] == franjas


def test_us002_ca1_reemplazar_quita_las_anteriores_y_no_toca_un_turno_existente(odontologa, sesion):
    consultorio = un_consultorio(sesion)
    profesional = un_profesional(
        sesion, consultorio, horario=(franja(0, "09:00", "13:00"), franja(0, "15:00", "19:00"))
    )
    turno = un_turno(
        sesion,
        paciente=un_paciente(sesion, consultorio),
        profesional=profesional,
        sillon=un_sillon(sesion, consultorio),
        prestacion=una_prestacion(sesion, consultorio),
        inicio=datetime(2026, 11, 2, 13, 0, tzinfo=timezone.utc),
    )
    url = f"/profesionales/{profesional.id}/horario"

    primera = odontologa.put(url, json={"franjas": [_f(1, "10:00", "14:00")]})
    segunda = odontologa.put(url, json={"franjas": []})

    assert primera.json()["franjas"] == [_f(1, "10:00", "14:00")]
    assert segunda.json()["franjas"] == []
    sesion.expire_all()
    assert sesion.get(TurnoModelo, turno.id).estado == "reservado"


def test_hor1_se_informan_juntas_las_superposiciones_de_varios_dias_y_una_franja_invertida(
    odontologa, sesion, fabrica_sesiones
):
    profesional = un_profesional(sesion, un_consultorio(sesion), horario=(franja(4, "09:00", "10:00"),))

    respuesta = odontologa.put(
        f"/profesionales/{profesional.id}/horario",
        json={
            "franjas": [
                _f(0, "09:00", "13:00"),
                _f(0, "12:59", "14:00"),
                _f(1, "10:00", "11:00"),
                _f(1, "10:30", "10:45"),
                _f(3, "18:00", "09:00"),
            ]
        },
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == ["RN-AG-16"]
    assert _errores(respuesta) == [
        ("franjas.1", "RN-AG-16", MENSAJE_SUPERPUESTA.format(i=1)),
        ("franjas.3", "RN-AG-16", MENSAJE_SUPERPUESTA.format(i=3)),
        ("franjas.4", "RN-AG-16", MENSAJE_INVERTIDA.format(i=4)),
    ]
    assert _guardadas(fabrica_sesiones, profesional.id) == [Franja(4, time(9, 0), time(10, 0))]


def test_hor1_en_una_cadena_de_tres_franjas_se_informan_las_dos_posteriores(odontologa, sesion):
    profesional = un_profesional(sesion, un_consultorio(sesion), horario=())

    respuesta = odontologa.put(
        f"/profesionales/{profesional.id}/horario",
        json={"franjas": [_f(2, "09:00", "13:00"), _f(2, "12:00", "16:00"), _f(2, "15:00", "19:00")]},
    )

    assert respuesta.status_code == 422
    assert _errores(respuesta) == [
        ("franjas.1", "RN-AG-16", MENSAJE_SUPERPUESTA.format(i=1)),
        ("franjas.2", "RN-AG-16", MENSAJE_SUPERPUESTA.format(i=2)),
    ]


def test_hor1_una_franja_de_duracion_cero_se_rechaza(odontologa, sesion):
    profesional = un_profesional(sesion, un_consultorio(sesion), horario=())

    respuesta = odontologa.put(f"/profesionales/{profesional.id}/horario", json={"franjas": [_f(0, "09:00", "09:00")]})

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == ["RN-AG-16"]
    assert _errores(respuesta) == [("franjas.0", "RN-AG-16", MENSAJE_INVERTIDA.format(i=0))]


def test_hor1_dos_franjas_identicas_del_mismo_dia_se_superponen(odontologa, sesion, fabrica_sesiones):
    profesional = un_profesional(sesion, un_consultorio(sesion), horario=(franja(5, "08:00", "09:00"),))

    respuesta = odontologa.put(
        f"/profesionales/{profesional.id}/horario",
        json={"franjas": [_f(0, "09:00", "13:00"), _f(0, "09:00", "13:00")]},
    )

    assert respuesta.status_code == 422
    assert _errores(respuesta) == [("franjas.1", "RN-AG-16", MENSAJE_SUPERPUESTA.format(i=1))]
    assert _guardadas(fabrica_sesiones, profesional.id) == [Franja(5, time(8, 0), time(9, 0))]


def test_us002_ca1_dia_y_hora_mal_formados_se_informan_juntos(odontologa, sesion, fabrica_sesiones):
    profesional = un_profesional(sesion, un_consultorio(sesion), horario=(franja(0, "09:00", "13:00"),))

    respuesta = odontologa.put(
        f"/profesionales/{profesional.id}/horario",
        json={"franjas": [_f(7, "09:00", "13:00"), _f(1, "09:00", "24:00")]},
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []
    assert sorted(e["campo"] for e in respuesta.json()["errores"]) == [
        "franjas.0.dia_semana",
        "franjas.1.hora_fin",
    ]
    assert _guardadas(fabrica_sesiones, profesional.id) == [Franja(0, time(9, 0), time(13, 0))]


def test_us002_ca1_con_formato_invalido_no_se_evalua_la_superposicion(odontologa, sesion):
    profesional = un_profesional(sesion, un_consultorio(sesion), horario=())

    respuesta = odontologa.put(
        f"/profesionales/{profesional.id}/horario",
        json={"franjas": [_f(0, "09:00", "13:00"), _f(0, "12:00", "16:00")], "color": "rojo"},
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []
    assert [e["campo"] for e in respuesta.json()["errores"]] == ["color"]


def test_us002_ca1_la_recepcionista_y_el_dueno_no_pueden_reemplazar_el_horario(
    recepcionista, dueno, sesion, fabrica_sesiones
):
    profesional = un_profesional(sesion, un_consultorio(sesion), horario=(franja(0, "09:00", "13:00"),))
    url = f"/profesionales/{profesional.id}/horario"

    for cliente in (recepcionista, dueno):
        respuesta = cliente.put(url, json={"franjas": [_f(1, "09:00", "13:00")]})
        assert respuesta.status_code == 403
        assert respuesta.json()["codigos"] == ["RN-AU-05"]
    assert _guardadas(fabrica_sesiones, profesional.id) == [Franja(0, time(9, 0), time(13, 0))]


def test_us002_ca1_el_permiso_y_la_entrada_se_evaluan_antes_que_el_profesional(
    recepcionista, odontologa, sesion
):
    un_consultorio(sesion)
    superpuestas = {"franjas": [_f(0, "09:00", "13:00"), _f(0, "12:00", "16:00")]}

    sin_permiso = recepcionista.put("/profesionales/999/horario", json=superpuestas)
    entrada = odontologa.put("/profesionales/999/horario", json=superpuestas)
    inexistente = odontologa.put("/profesionales/999/horario", json={"franjas": [_f(0, "09:00", "13:00")]})

    assert (sin_permiso.status_code, sin_permiso.json()["codigos"]) == (403, ["RN-AU-05"])
    assert (entrada.status_code, entrada.json()["codigos"]) == (422, ["RN-AG-16"])
    assert (inexistente.status_code, inexistente.json()["codigos"]) == (404, ["RN-GL-04"])


def test_us002_ca1_sin_sesion_se_responde_401_antes_que_la_entrada(app, sesion):
    profesional = un_profesional(sesion, un_consultorio(sesion))

    respuesta = TestClient(app).put(
        f"/profesionales/{profesional.id}/horario", json={"franjas": [_f(9, "09:00", "13:00")]}
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["codigos"] == ["RN-AU-03"]


def test_us002_ca1_sin_sesion_no_se_listan_los_profesionales(app, sesion):
    un_profesional(sesion, un_consultorio(sesion))

    respuesta = TestClient(app).get("/profesionales")

    assert respuesta.status_code == 401
    assert respuesta.json()["codigos"] == ["RN-AU-03"]


def test_us002_ca1_el_horario_de_un_profesional_inactivo_se_puede_editar(odontologa, sesion):
    consultorio = un_consultorio(sesion)
    un_profesional(sesion, consultorio)
    inactivo = un_profesional(sesion, consultorio, activo=False, horario=())
    url = f"/profesionales/{inactivo.id}/horario"

    guardado = odontologa.put(url, json={"franjas": [_f(0, "09:00", "13:00")]})
    leido = odontologa.get(url)

    assert (guardado.status_code, leido.status_code) == (200, 200)
    assert guardado.json()["franjas"] == leido.json()["franjas"] == [_f(0, "09:00", "13:00")]


def test_us002_ca1_un_profesional_de_otro_consultorio_responde_404(odontologa, sesion, fabrica_sesiones):
    propio = un_consultorio(sesion)
    un_profesional(sesion, propio, nombre="Profesional propio")
    ajeno = un_profesional(sesion, un_consultorio(sesion), nombre="Profesional ajeno", horario=())
    url = f"/profesionales/{ajeno.id}/horario"

    leido = odontologa.get(url)
    reemplazado = odontologa.put(url, json={"franjas": [_f(0, "09:00", "13:00")]})

    for respuesta in (leido, reemplazado):
        assert respuesta.status_code == 404
        assert respuesta.json()["codigos"] == ["RN-GL-04"]
        assert respuesta.json()["referencias"] == [
            {"recurso": "profesional", "recurso_id": ajeno.id, "motivo": "inexistente"}
        ]
    assert _guardadas(fabrica_sesiones, ajeno.id) == []
    assert [p["nombre"] for p in odontologa.get("/profesionales").json()] == ["Profesional propio"]
