"""Lectura de turnos ocupados del repositorio real sobre SQLite en memoria (E11, design I8)."""
import pytest
from sqlalchemy import Engine, event
from sqlalchemy.orm import Session

from app.domain.agenda.intervalo import Intervalo
from app.domain.turnos.estados import EstadoTurno
from app.infrastructure.repositories.agenda import RepositorioAgendaSqlAlchemy
from tests.conftest import a_las
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
)


@pytest.fixture
def mundo(sesion: Session) -> dict:
    consultorio = un_consultorio(sesion)
    return {
        "paciente": un_paciente(sesion, consultorio),
        "prestacion": una_prestacion(sesion, consultorio),  # 30 minutos
        "profesional": un_profesional(sesion, consultorio, nombre="Profesional A"),
        "otro_profesional": un_profesional(sesion, consultorio, nombre="Profesional B"),
        "sillon": un_sillon(sesion, consultorio, nombre="Sillón 1"),
        "otro_sillon": un_sillon(sesion, consultorio, nombre="Sillón 2"),
    }


def _turno(sesion: Session, mundo: dict, profesional: str, sillon: str, inicio, **kw):
    return un_turno(
        sesion,
        paciente=mundo["paciente"],
        profesional=mundo[profesional],
        sillon=mundo[sillon],
        prestacion=mundo["prestacion"],
        inicio=inicio,
        **kw,
    )


def _ids(ocupados) -> list[int]:
    return sorted(o.turno_id for o in ocupados)


def test_trae_los_turnos_que_chocan_por_profesional_por_sillon_o_por_ambos(
    sesion: Session, mundo: dict
) -> None:
    por_profesional = _turno(sesion, mundo, "profesional", "otro_sillon", a_las(10, 15))
    por_sillon = _turno(sesion, mundo, "otro_profesional", "sillon", a_las(9, 45))
    por_ambos = _turno(sesion, mundo, "profesional", "sillon", a_las(10))
    contiguo = _turno(sesion, mundo, "profesional", "sillon", a_las(10, 30))
    anterior = _turno(sesion, mundo, "profesional", "sillon", a_las(9, 30))
    ajeno = _turno(sesion, mundo, "otro_profesional", "otro_sillon", a_las(10))

    ocupados = RepositorioAgendaSqlAlchemy(sesion).ocupados_en_el_intervalo(
        mundo["profesional"].id, mundo["sillon"].id, Intervalo(a_las(10), a_las(10, 30))
    )

    assert _ids(ocupados.del_profesional) == sorted([por_profesional.id, por_ambos.id])
    assert _ids(ocupados.del_sillon) == sorted([por_sillon.id, por_ambos.id])
    ids_traidos = set(_ids(ocupados.del_profesional)) | set(_ids(ocupados.del_sillon))
    assert not ids_traidos & {contiguo.id, anterior.id, ajeno.id}


def test_devuelve_turnos_de_cualquier_estado_para_que_decida_el_dominio(
    sesion: Session, mundo: dict
) -> None:
    cancelado = _turno(sesion, mundo, "profesional", "sillon", a_las(10), estado="cancelado_paciente")

    ocupados = RepositorioAgendaSqlAlchemy(sesion).ocupados_en_el_intervalo(
        mundo["profesional"].id, mundo["sillon"].id, Intervalo(a_las(10), a_las(10, 30))
    )

    assert [(o.turno_id, o.estado) for o in ocupados.del_profesional] == [
        (cancelado.id, EstadoTurno.CANCELADO_PACIENTE)
    ]
    assert [o.turno_id for o in ocupados.del_sillon] == [cancelado.id]


def test_sin_turnos_que_intersequen_devuelve_dos_listas_vacias(
    sesion: Session, mundo: dict
) -> None:
    ocupados = RepositorioAgendaSqlAlchemy(sesion).ocupados_en_el_intervalo(
        mundo["profesional"].id, mundo["sillon"].id, Intervalo(a_las(10), a_las(10, 30))
    )

    assert list(ocupados.del_profesional) == []
    assert list(ocupados.del_sillon) == []


def test_lee_los_conflictos_con_una_sola_sentencia(
    engine: Engine, sesion: Session, mundo: dict
) -> None:
    _turno(sesion, mundo, "profesional", "otro_sillon", a_las(10))
    _turno(sesion, mundo, "otro_profesional", "sillon", a_las(10))
    sentencias: list[str] = []

    def registrar(conexion, cursor, sentencia, parametros, contexto, varias):
        sentencias.append(sentencia)

    event.listen(engine, "before_cursor_execute", registrar)
    try:
        RepositorioAgendaSqlAlchemy(sesion).ocupados_en_el_intervalo(
            mundo["profesional"].id, mundo["sillon"].id, Intervalo(a_las(10), a_las(10, 30))
        )
    finally:
        event.remove(engine, "before_cursor_execute", registrar)

    assert len([s for s in sentencias if s.lstrip().upper().startswith("SELECT")]) == 1


def _sentencias_que_emite(engine: Engine, accion) -> list[str]:
    sentencias: list[str] = []

    def registrar(conexion, cursor, sentencia, parametros, contexto, varias):
        sentencias.append(" ".join(sentencia.split()))

    event.listen(engine, "before_cursor_execute", registrar)
    try:
        accion()
    finally:
        event.remove(engine, "before_cursor_execute", registrar)
    return sentencias


def test_bloquear_recursos_emite_primero_el_profesional_y_despues_el_sillon(
    engine: Engine, sesion: Session, mundo: dict
) -> None:
    repositorio = RepositorioAgendaSqlAlchemy(sesion)

    sentencias = _sentencias_que_emite(
        engine,
        lambda: repositorio.bloquear_recursos(mundo["profesional"].id, mundo["sillon"].id),
    )

    assert len(sentencias) == 2
    assert " FROM profesional " in sentencias[0] + " "
    assert " FROM sillon " in sentencias[1] + " "


def test_bloquear_recursos_en_sqlite_no_emite_clausula_de_bloqueo(
    engine: Engine, sesion: Session, mundo: dict
) -> None:
    repositorio = RepositorioAgendaSqlAlchemy(sesion)

    sentencias = _sentencias_que_emite(
        engine,
        lambda: repositorio.bloquear_recursos(mundo["otro_profesional"].id, mundo["otro_sillon"].id),
    )

    assert sentencias  # se emitieron
    assert not any("FOR " in s.upper() for s in sentencias)
