"""``/bloqueos`` por HTTP con ``TestClient`` sobre ``crear_app(engine)`` (US-003 CA-1 y CA-2; RN-AG-04b, RN-AG-17).

Sin dobles: sesión, repositorios y firmador son los reales y cada rol manda un access token real (D211);
solo el reloj se sustituye. Los horarios son UTC del lunes 2026-11-02 (``a_las``); el consultorio es
America/Argentina/Buenos_Aires (UTC-3). Los turnos y los bloqueos ajenos se guardan directo en la base.
Todos los datos son ficticios (RN-PR-01).
"""
from dataclasses import dataclass
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_reloj
from app.domain.acceso.roles import Rol
from app.infrastructure.configuracion import ConfiguracionDeSesion
from app.infrastructure.db.modelos import BloqueoModelo, EventoTurnoModelo, TurnoModelo, UsuarioModelo
from app.main import crear_app
from tests.conftest import SECRETO_DE_PRUEBA, a_las, reloj_fijo, token_de
from tests.factories import (
    un_bloqueo,
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
    un_usuario,
)

ZONA = "America/Argentina/Buenos_Aires"
PROBLEMA_JSON = "application/problem+json"


def iso(momento: datetime) -> str:
    return momento.strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Mundo:
    consultorio: object
    profesional: object
    sillon: object
    paciente: object
    prestacion: object
    odontologa: UsuarioModelo
    recepcionista: UsuarioModelo
    dueno: UsuarioModelo


@pytest.fixture
def app(engine):
    app = crear_app(engine, ConfiguracionDeSesion(SECRETO_DE_PRUEBA, rondas_bcrypt=4))
    app.dependency_overrides[get_reloj] = lambda: reloj_fijo
    return app


@pytest.fixture
def cliente(app) -> TestClient:
    return TestClient(app)


@pytest.fixture
def mundo(sesion: Session) -> Mundo:
    consultorio = un_consultorio(sesion)
    return Mundo(
        consultorio=consultorio,
        profesional=un_profesional(sesion, consultorio, nombre="Profesional 1"),
        sillon=un_sillon(sesion, consultorio, nombre="Sillón 1"),
        paciente=un_paciente(sesion, consultorio),
        prestacion=una_prestacion(sesion, consultorio),  # 30 minutos
        odontologa=un_usuario(sesion, consultorio, roles=(Rol.ODONTOLOGO,)),
        recepcionista=un_usuario(sesion, consultorio, roles=(Rol.RECEPCIONISTA,)),
        dueno=un_usuario(sesion, consultorio, roles=(Rol.DUENO,)),
    )


def con(usuario: UsuarioModelo) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_de(usuario.id)}"}


def un_turno_del(sesion: Session, mundo: Mundo, inicio: datetime, **kw) -> TurnoModelo:
    return un_turno(
        sesion,
        paciente=mundo.paciente,
        profesional=kw.pop("profesional", mundo.profesional),
        sillon=kw.pop("sillon", mundo.sillon),
        prestacion=mundo.prestacion,
        inicio=inicio,
        **kw,
    )


def cuerpo(desde: datetime, hasta: datetime, motivo: str = "Ausencia", **ids) -> dict:
    return {"inicio": iso(desde), "fin": iso(hasta), "motivo": motivo, **ids}


def cuantos(sesion: Session, modelo) -> int:
    sesion.expire_all()
    return sesion.scalar(select(func.count()).select_from(modelo))


# --- US-003 CA-1 ------------------------------------------------------------------------------------
def test_us003_ca1_la_odontologa_bloquea_al_profesional_por_vacaciones(cliente, mundo) -> None:
    desde, hasta = datetime.fromisoformat("2026-11-09T03:00:00+00:00"), datetime.fromisoformat("2026-11-14T03:00:00+00:00")

    respuesta = cliente.post(
        "/bloqueos",
        json=cuerpo(desde, hasta, "Vacaciones", profesional_id=mundo.profesional.id),
        headers=con(mundo.odontologa),
    )

    assert respuesta.status_code == 201
    esperado = {
        "id": respuesta.json()["id"],
        "alcance": "profesional",
        "profesional_id": mundo.profesional.id,
        "sillon_id": None,
        "inicio": "2026-11-09T03:00:00Z",
        "fin": "2026-11-14T03:00:00Z",
        "motivo": "Vacaciones",
        "creado_por": mundo.odontologa.id,
        "turnos_afectados": [],
    }
    assert respuesta.json() == esperado
    listado = cliente.get("/bloqueos", headers=con(mundo.odontologa)).json()
    assert listado["bloqueos"] == [{k: v for k, v in esperado.items() if k != "turnos_afectados"}]


def test_us003_ca2_el_bloqueo_del_profesional_lista_sus_dos_turnos_activos(cliente, mundo, sesion) -> None:
    tarde = un_turno_del(sesion, mundo, a_las(14), estado="confirmado")
    temprano = un_turno_del(sesion, mundo, a_las(13))

    respuesta = cliente.post(
        "/bloqueos",
        json=cuerpo(a_las(12), a_las(16), profesional_id=mundo.profesional.id),
        headers=con(mundo.odontologa),
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["turnos_afectados"] == [
        {
            "id": turno.id,
            "inicio": iso(turno.inicio),
            "fin": iso(turno.fin),
            "estado": estado,
            "profesional_id": mundo.profesional.id,
            "sillon_id": mundo.sillon.id,
            "paciente_id": mundo.paciente.id,
        }
        for turno, estado in ((temprano, "reservado"), (tarde, "confirmado"))
    ]
    sesion.expire_all()
    assert [t.estado for t in sesion.scalars(select(TurnoModelo).order_by(TurnoModelo.id))] == ["confirmado", "reservado"]
    assert cuantos(sesion, EventoTurnoModelo) == 0


@pytest.mark.parametrize(("inicio", "fin"), [(a_las(15), a_las(13)), (a_las(13), a_las(13))])
def test_us003_ca1_un_bloqueo_que_no_termina_despues_de_empezar_se_rechaza(cliente, mundo, sesion, inicio, fin) -> None:
    respuesta = cliente.post(
        "/bloqueos",
        json=cuerpo(inicio, fin, profesional_id=mundo.profesional.id),
        headers=con(mundo.odontologa),
    )

    assert respuesta.status_code == 422
    assert respuesta.headers["content-type"].startswith(PROBLEMA_JSON)
    assert respuesta.json()["codigos"] == ["RN-AG-17"]
    assert [(e["campo"], e["codigo"]) for e in respuesta.json()["errores"]] == [("fin", "RN-AG-17")]
    assert cuantos(sesion, BloqueoModelo) == 0


def test_us003_ca1_la_recepcionista_lista_los_bloqueos(cliente, mundo, sesion) -> None:
    feriado = un_bloqueo(
        sesion,
        mundo.consultorio,
        inicio=datetime.fromisoformat("2026-11-23T03:00:00+00:00"),
        fin=datetime.fromisoformat("2026-11-24T03:00:00+00:00"),
        motivo="Feriado",
    )
    ausencia = un_bloqueo(sesion, mundo.consultorio, inicio=a_las(13), fin=a_las(15), profesional=mundo.profesional)

    respuesta = cliente.get("/bloqueos", headers=con(mundo.recepcionista))

    assert respuesta.status_code == 200
    cuerpo_ = respuesta.json()
    assert cuerpo_["zona_horaria"] == ZONA
    assert [(b["id"], b["alcance"]) for b in cuerpo_["bloqueos"]] == [
        (ausencia.id, "profesional"),
        (feriado.id, "consultorio"),
    ]
    assert all("turnos_afectados" not in b for b in cuerpo_["bloqueos"])


def test_us003_ca1_la_odontologa_elimina_un_bloqueo(cliente, mundo, sesion) -> None:
    bloqueo = un_bloqueo(sesion, mundo.consultorio, inicio=a_las(13), fin=a_las(15), profesional=mundo.profesional)
    turno = un_turno_del(sesion, mundo, a_las(13))

    respuesta = cliente.delete(f"/bloqueos/{bloqueo.id}", headers=con(mundo.odontologa))

    assert respuesta.status_code == 204
    assert respuesta.content == b""
    assert cliente.get("/bloqueos", headers=con(mundo.odontologa)).json()["bloqueos"] == []
    sesion.expire_all()
    assert sesion.get(TurnoModelo, turno.id).estado == "reservado"


# --- US-003 CA-1: alcances, bordes del alta ----------------------------------------------------------
def test_us003_ca1_un_bloqueo_del_sillon_acepta_minutos_que_no_son_multiplo_de_5(cliente, mundo) -> None:
    respuesta = cliente.post(
        "/bloqueos",
        json=cuerpo(a_las(13, 7), a_las(14, 53), "Mantenimiento del sillón", sillon_id=mundo.sillon.id),
        headers=con(mundo.odontologa),
    )

    assert respuesta.status_code == 201
    assert (respuesta.json()["alcance"], respuesta.json()["sillon_id"], respuesta.json()["profesional_id"]) == (
        "sillon",
        mundo.sillon.id,
        None,
    )
    assert (respuesta.json()["inicio"], respuesta.json()["fin"]) == ("2026-11-02T13:07:00Z", "2026-11-02T14:53:00Z")


def test_us003_ca1_un_bloqueo_de_todo_el_consultorio_por_un_feriado(cliente, mundo) -> None:
    desde, hasta = datetime.fromisoformat("2026-11-23T03:00:00+00:00"), datetime.fromisoformat("2026-11-24T03:00:00+00:00")

    respuesta = cliente.post("/bloqueos", json=cuerpo(desde, hasta, "Feriado"), headers=con(mundo.odontologa))

    assert respuesta.status_code == 201
    assert (respuesta.json()["alcance"], respuesta.json()["profesional_id"], respuesta.json()["sillon_id"]) == (
        "consultorio",
        None,
        None,
    )


def test_us003_ca1_un_bloqueo_que_se_superpone_con_otro_se_acepta(cliente, mundo, sesion) -> None:
    un_bloqueo(sesion, mundo.consultorio, inicio=a_las(13), fin=a_las(15), profesional=mundo.profesional)

    respuesta = cliente.post(
        "/bloqueos",
        json=cuerpo(a_las(14), a_las(16), profesional_id=mundo.profesional.id),
        headers=con(mundo.odontologa),
    )

    assert respuesta.status_code == 201
    assert len(cliente.get("/bloqueos", headers=con(mundo.odontologa)).json()["bloqueos"]) == 2


def test_us003_ca1_un_bloqueo_en_el_pasado_se_acepta_lista_sus_turnos_activos_y_se_elimina(
    app, mundo, sesion
) -> None:
    ahora = datetime.fromisoformat("2026-11-10T12:00:00+00:00")
    app.dependency_overrides[get_reloj] = lambda: (lambda: ahora)
    cliente = TestClient(app)
    cabecera = {"Authorization": "Bearer " + token_de(mundo.odontologa.id, emitido_en=ahora)}
    un_turno_del(sesion, mundo, a_las(13), estado="atendido")
    reservado = un_turno_del(sesion, mundo, a_las(14))

    creado = cliente.post(
        "/bloqueos",
        json=cuerpo(a_las(12), a_las(16), profesional_id=mundo.profesional.id),
        headers=cabecera,
    )

    assert creado.status_code == 201
    assert [t["id"] for t in creado.json()["turnos_afectados"]] == [reservado.id]
    borrado = cliente.delete("/bloqueos/" + str(creado.json()["id"]), headers=cabecera)
    assert borrado.status_code == 204


@pytest.mark.parametrize(
    ("motivo", "estado", "guardado"),
    [("a" * 200, 201, "a" * 200), ("  Vacaciones  ", 201, "Vacaciones"), ("a" * 201, 422, None)],
)
def test_us003_ca1_el_motivo_admite_hasta_200_caracteres_y_se_guarda_sin_espacios_de_mas(
    cliente, mundo, sesion, motivo, estado, guardado
) -> None:
    respuesta = cliente.post(
        "/bloqueos",
        json=cuerpo(a_las(13), a_las(15), motivo, profesional_id=mundo.profesional.id),
        headers=con(mundo.odontologa),
    )

    assert respuesta.status_code == estado
    if guardado is None:
        assert respuesta.json()["codigos"] == []
        assert [e["campo"] for e in respuesta.json()["errores"]] == ["motivo"]
        assert cuantos(sesion, BloqueoModelo) == 0
    else:
        assert respuesta.json()["motivo"] == guardado
        assert cuantos(sesion, BloqueoModelo) == 1


# --- US-003 CA-2: turnos afectados, bordes ------------------------------------------------------------
def test_us003_ca2_los_turnos_no_activos_y_los_contiguos_no_se_listan(cliente, mundo, sesion) -> None:
    un_turno_del(sesion, mundo, a_las(13), estado="cancelado_paciente")
    un_turno_del(sesion, mundo, a_las(13, 30), estado="atendido")
    un_turno_del(sesion, mundo, a_las(11, 30))  # termina justo cuando empieza el bloqueo
    un_turno_del(sesion, mundo, a_las(16))  # empieza justo cuando termina
    un_minuto = un_turno_del(sesion, mundo, a_las(15, 59))

    respuesta = cliente.post(
        "/bloqueos",
        json=cuerpo(a_las(12), a_las(16), profesional_id=mundo.profesional.id),
        headers=con(mundo.odontologa),
    )

    assert [t["id"] for t in respuesta.json()["turnos_afectados"]] == [un_minuto.id]


def test_us003_ca2_cada_alcance_lista_sus_propios_turnos(cliente, mundo, sesion) -> None:
    otro_profesional = un_profesional(sesion, mundo.consultorio, nombre="Profesional 2")
    otro_sillon = un_sillon(sesion, mundo.consultorio, nombre="Sillón 2")
    del_primero = un_turno_del(sesion, mundo, a_las(13))
    del_segundo = un_turno_del(sesion, mundo, a_las(13), profesional=otro_profesional, sillon=otro_sillon)

    def afectados(**ids) -> list[int]:
        respuesta = cliente.post("/bloqueos", json=cuerpo(a_las(12), a_las(16), **ids), headers=con(mundo.odontologa))
        return sorted(t["id"] for t in respuesta.json()["turnos_afectados"])

    assert afectados(sillon_id=mundo.sillon.id) == [del_primero.id]
    assert afectados(profesional_id=otro_profesional.id) == [del_segundo.id]
    assert afectados() == sorted([del_primero.id, del_segundo.id])


def test_us003_ca2_un_turno_de_otro_consultorio_no_se_lista(cliente, mundo, sesion) -> None:
    ajeno = un_consultorio(sesion)
    un_turno(
        sesion,
        paciente=un_paciente(sesion, ajeno),
        profesional=un_profesional(sesion, ajeno),
        sillon=un_sillon(sesion, ajeno),
        prestacion=una_prestacion(sesion, ajeno),
        inicio=a_las(13),
    )

    respuesta = cliente.post("/bloqueos", json=cuerpo(a_las(12), a_las(16)), headers=con(mundo.odontologa))

    assert respuesta.status_code == 201
    assert respuesta.json()["turnos_afectados"] == []


# --- Validación de entrada y formato ------------------------------------------------------------------
def _referencias(respuesta) -> list[tuple]:
    return [(r["recurso"], r["recurso_id"], r["motivo"]) for r in respuesta.json()["referencias"]]


def test_us003_ca1_fecha_sin_zona_y_referencias_invalidas_se_informan_juntas(cliente, mundo, sesion) -> None:
    inactivo = un_sillon(sesion, mundo.consultorio, nombre="Sillón inactivo", activo=False)

    sin_zona = cliente.post(
        "/bloqueos",
        json={"profesional_id": 999, "inicio": "2026-11-02T13:00:00", "fin": iso(a_las(15)), "motivo": "Ausencia"},
        headers=con(mundo.odontologa),
    )
    con_sillon_inactivo = cliente.post(
        "/bloqueos", json=cuerpo(a_las(13), a_las(15), sillon_id=inactivo.id), headers=con(mundo.odontologa)
    )

    assert sin_zona.status_code == 422
    assert sin_zona.json()["codigos"] == ["RN-GL-01", "RN-GL-04"]
    assert _referencias(sin_zona) == [("profesional", 999, "inexistente")]
    assert con_sillon_inactivo.status_code == 422
    assert con_sillon_inactivo.json()["codigos"] == ["RN-GL-04"]
    assert _referencias(con_sillon_inactivo) == [("sillon", inactivo.id, "inactivo")]
    assert cuantos(sesion, BloqueoModelo) == 0


def test_us003_ca1_un_profesional_de_otro_consultorio_cuenta_como_inexistente(cliente, mundo, sesion) -> None:
    ajeno = un_profesional(sesion, un_consultorio(sesion), nombre="Profesional ajeno")

    respuesta = cliente.post(
        "/bloqueos", json=cuerpo(a_las(13), a_las(15), profesional_id=ajeno.id), headers=con(mundo.odontologa)
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == ["RN-GL-04"]
    assert _referencias(respuesta) == [("profesional", ajeno.id, "inexistente")]


def test_us003_ca1_la_referencia_invalida_y_la_fecha_invertida_se_informan_juntas(cliente, mundo) -> None:
    respuesta = cliente.post(
        "/bloqueos",
        json={"profesional_id": 999, "inicio": iso(a_las(15)), "fin": iso(a_las(13)), "motivo": "Ausencia"},
        headers=con(mundo.odontologa),
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == ["RN-GL-04", "RN-AG-17"]


def test_us003_ca1_el_profesional_y_el_sillon_a_la_vez_son_un_error_de_formato(cliente, mundo, sesion) -> None:
    respuesta = cliente.post(
        "/bloqueos",
        json=cuerpo(a_las(13), a_las(15), profesional_id=mundo.profesional.id, sillon_id=mundo.sillon.id),
        headers=con(mundo.odontologa),
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []
    assert cuantos(sesion, BloqueoModelo) == 0


def test_us003_ca1_motivo_vacio_y_campo_de_mas_se_informan_juntos_antes_que_la_fecha_invertida(
    cliente, mundo
) -> None:
    respuesta = cliente.post(
        "/bloqueos",
        json={**cuerpo(a_las(15), a_las(13), "   "), "color": "rojo"},
        headers=con(mundo.odontologa),
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigos"] == []
    assert sorted(e["campo"] for e in respuesta.json()["errores"]) == ["color", "motivo"]


# --- Listado y eliminación, bordes ---------------------------------------------------------------------
def test_us003_ca1_un_bloqueo_de_otro_consultorio_no_se_lista(cliente, mundo, sesion) -> None:
    un_bloqueo(sesion, un_consultorio(sesion), inicio=a_las(13), fin=a_las(15))

    respuesta = cliente.get("/bloqueos", headers=con(mundo.dueno))

    assert respuesta.status_code == 200
    assert respuesta.json()["bloqueos"] == []


def test_us003_ca1_un_bloqueo_inexistente_o_de_otro_consultorio_responde_404(cliente, mundo, sesion) -> None:
    ajeno = un_bloqueo(sesion, un_consultorio(sesion), inicio=a_las(13), fin=a_las(15))
    cabecera = con(mundo.odontologa)

    inexistente = cliente.delete("/bloqueos/999", headers=cabecera)
    de_otro = cliente.delete("/bloqueos/" + str(ajeno.id), headers=cabecera)
    no_entero = cliente.delete("/bloqueos/abc", headers=cabecera)

    for respuesta, id_ in ((inexistente, 999), (de_otro, ajeno.id)):
        assert respuesta.status_code == 404
        assert respuesta.json()["codigos"] == ["RN-GL-04"]
        assert _referencias(respuesta) == [("bloqueo", id_, "inexistente")]
    assert (no_entero.status_code, no_entero.json()["codigos"]) == (422, [])
    assert cuantos(sesion, BloqueoModelo) == 1


# --- Permisos y orden de evaluación -----------------------------------------------------------------------
@pytest.mark.parametrize("rol", ["recepcionista", "dueno"])
def test_us003_ca1_la_recepcionista_y_el_dueno_no_pueden_crear_ni_eliminar_bloqueos(
    cliente, mundo, sesion, rol
) -> None:
    bloqueo = un_bloqueo(sesion, mundo.consultorio, inicio=a_las(13), fin=a_las(15), profesional=mundo.profesional)
    usuario = getattr(mundo, rol)

    crear = cliente.post(
        "/bloqueos", json=cuerpo(a_las(13), a_las(15), profesional_id=mundo.profesional.id), headers=con(usuario)
    )
    eliminar = cliente.delete("/bloqueos/" + str(bloqueo.id), headers=con(usuario))

    for respuesta in (crear, eliminar):
        assert respuesta.status_code == 403
        assert respuesta.json()["codigos"] == ["RN-AU-05"]
    assert cuantos(sesion, BloqueoModelo) == 1


def test_us003_ca1_sin_sesion_se_responde_401_antes_que_la_entrada(cliente, mundo) -> None:
    crear = cliente.post("/bloqueos", json=cuerpo(a_las(15), a_las(13)))
    listar = cliente.get("/bloqueos")
    eliminar = cliente.delete("/bloqueos/999")

    for respuesta in (crear, listar, eliminar):
        assert respuesta.status_code == 401
        assert respuesta.json()["codigos"] == ["RN-AU-03"]


def test_us003_ca1_el_permiso_se_evalua_antes_que_la_entrada_y_que_el_bloqueo_de_la_url(cliente, mundo) -> None:
    crear = cliente.post("/bloqueos", json=cuerpo(a_las(15), a_las(13)), headers=con(mundo.recepcionista))
    eliminar = cliente.delete("/bloqueos/999", headers=con(mundo.recepcionista))

    for respuesta in (crear, eliminar):
        assert (respuesta.status_code, respuesta.json()["codigos"]) == (403, ["RN-AU-05"])
