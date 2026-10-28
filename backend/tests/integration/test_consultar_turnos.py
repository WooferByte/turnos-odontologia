"""Agenda del día y lectura de un turno sobre SQLite en memoria (US-011 CA-1; AGE-1, AGE-3; RN-GL-01, RN-PR-01)."""
from dataclasses import fields
from datetime import date, datetime, timedelta

import pytest

from app.application.consultar_turnos import agenda_del_dia, turno_de_la_agenda
from app.domain.errors import TurnoNoEncontrado
from app.domain.tiempo import UTC
from tests.conftest import a_las, reloj_fijo
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
    un_usuario,
)

DIA = date(2026, 11, 2)


def _escenario(sesion):
    consultorio = un_consultorio(sesion)
    return {
        "consultorio": consultorio,
        "usuario": un_usuario(sesion, consultorio),
        "profesional": un_profesional(sesion, consultorio),
        "sillon": un_sillon(sesion, consultorio),
        "ana": un_paciente(sesion, consultorio, nombre="Ana", apellido="Ejemplo"),
        "bruno": un_paciente(sesion, consultorio, nombre="Bruno", apellido="Ficticio"),
        "carla": un_paciente(sesion, consultorio, nombre="Carla", apellido="Inventada"),
        "consulta": una_prestacion(sesion, consultorio, nombre="Consulta / control", duracion_minutos=30, color="#1E88E5"),
        "limpieza": una_prestacion(sesion, consultorio, nombre="Limpieza", duracion_minutos=45, color="#43A047"),
        "obturacion": una_prestacion(sesion, consultorio, nombre="Obturación", duracion_minutos=60, color="#FB8C00"),
    }


def _turno(sesion, datos, paciente, prestacion, inicio, **kw):
    return un_turno(
        sesion,
        paciente=datos[paciente],
        profesional=datos["profesional"],
        sillon=datos["sillon"],
        prestacion=datos[prestacion],
        inicio=inicio,
        **kw,
    )


def test_age1a_agenda_del_dia_ordena_por_inicio_con_paciente_y_prestacion(sesion, uow):
    datos = _escenario(sesion)
    _turno(sesion, datos, "carla", "obturacion", a_las(14), estado="confirmado")
    _turno(sesion, datos, "ana", "consulta", a_las(12))
    _turno(sesion, datos, "bruno", "limpieza", a_las(13))

    agenda = agenda_del_dia(DIA, datos["usuario"].id, uow, reloj_fijo)

    assert agenda.fecha == DIA
    assert agenda.zona_horaria == "America/Argentina/Buenos_Aires"
    assert [t.paciente_apellido for t in agenda.turnos] == ["Ejemplo", "Ficticio", "Inventada"]
    primero = agenda.turnos[0]
    assert (primero.paciente_nombre, primero.prestacion_nombre, primero.prestacion_color) == (
        "Ana",
        "Consulta / control",
        "#1E88E5",
    )
    assert (primero.inicio, primero.fin, primero.duracion_minutos, primero.estado) == (
        a_las(12),
        a_las(12, 30),
        30,
        "reservado",
    )
    assert agenda.turnos[2].estado == "confirmado"
    # RN-PR-01: la lectura no trae el teléfono ni ningún otro dato del paciente.
    assert not any("telefono" in campo.name for campo in fields(primero))


def test_age3c_la_agenda_no_trae_turnos_de_otro_consultorio(sesion, uow):
    datos = _escenario(sesion)
    otro = _escenario(sesion)
    _turno(sesion, datos, "ana", "consulta", a_las(12))
    ajeno = _turno(sesion, otro, "bruno", "limpieza", a_las(12))

    agenda = agenda_del_dia(DIA, datos["usuario"].id, uow, reloj_fijo)

    assert [t.paciente_apellido for t in agenda.turnos] == ["Ejemplo"]
    assert ajeno.id not in [t.id for t in agenda.turnos]


def _reloj(texto):
    instante = datetime.fromisoformat(texto).replace(tzinfo=UTC)
    return lambda: instante


def test_age1c_sin_fecha_usa_hoy_del_consultorio(sesion, uow):
    datos = _escenario(sesion)
    _turno(sesion, datos, "ana", "consulta", a_las(12))

    antes_de_medianoche = agenda_del_dia(None, datos["usuario"].id, uow, _reloj("2026-11-03T01:00:00"))
    despues_de_medianoche = agenda_del_dia(None, datos["usuario"].id, uow, _reloj("2026-11-03T03:00:00"))

    assert antes_de_medianoche.fecha == DIA
    assert [t.paciente_apellido for t in antes_de_medianoche.turnos] == ["Ejemplo"]
    assert despues_de_medianoche.fecha == date(2026, 11, 3)
    assert despues_de_medianoche.turnos == []


def test_age1d_un_turno_cancelado_aparece(sesion, uow):
    datos = _escenario(sesion)
    _turno(sesion, datos, "bruno", "limpieza", a_las(13), estado="cancelado_paciente")

    agenda = agenda_del_dia(DIA, datos["usuario"].id, uow, reloj_fijo)

    assert [t.estado for t in agenda.turnos] == ["cancelado_paciente"]


def test_age1d_una_prestacion_inactiva_aparece(sesion, uow):
    datos = _escenario(sesion)
    _turno(sesion, datos, "ana", "obturacion", a_las(15))
    datos["obturacion"].activa = False
    sesion.commit()

    agenda = agenda_del_dia(DIA, datos["usuario"].id, uow, reloj_fijo)

    assert [(t.prestacion_nombre, t.prestacion_color) for t in agenda.turnos] == [("Obturación", "#FB8C00")]


def test_age1d_un_dia_sin_turnos_da_una_lista_vacia(sesion, uow):
    datos = _escenario(sesion)
    _turno(sesion, datos, "ana", "consulta", a_las(12))

    agenda = agenda_del_dia(date(2026, 11, 5), datos["usuario"].id, uow, reloj_fijo)

    assert agenda.fecha == date(2026, 11, 5)
    assert agenda.turnos == []


def test_age1f_a_igual_inicio_ordena_por_id(sesion, uow):
    datos = _escenario(sesion)
    inicio = a_las(13) + timedelta(days=2)
    _turno(sesion, datos, "ana", "limpieza", inicio, id=20)
    # Mismo horario y recursos: la base de pruebas (SQLite) no tiene la exclusión de PostgreSQL.
    _turno(sesion, datos, "bruno", "limpieza", inicio, id=10, estado="cancelado_paciente")

    agenda = agenda_del_dia(date(2026, 11, 4), datos["usuario"].id, uow, reloj_fijo)

    assert [t.id for t in agenda.turnos] == [10, 20]


def test_age2a_turno_de_la_agenda_devuelve_el_turno_con_paciente_y_prestacion(sesion, uow):
    datos = _escenario(sesion)
    turno = _turno(sesion, datos, "bruno", "limpieza", a_las(13))

    leido = turno_de_la_agenda(turno.id, datos["usuario"].id, uow)

    assert (leido.id, leido.paciente_nombre, leido.prestacion_nombre, leido.duracion_minutos) == (
        turno.id,
        "Bruno",
        "Limpieza",
        45,
    )


def test_age3c_turno_de_la_agenda_de_otro_consultorio_no_se_encuentra(sesion, uow):
    datos = _escenario(sesion)
    otro = _escenario(sesion)
    ajeno = _turno(sesion, otro, "bruno", "limpieza", a_las(12))

    with pytest.raises(TurnoNoEncontrado) as error:
        turno_de_la_agenda(ajeno.id, datos["usuario"].id, uow)

    assert error.value.codigos == ["RN-GL-04"]
    assert error.value.referencias[0].recurso_id == ajeno.id


def test_age2b_turno_de_la_agenda_inexistente_no_se_encuentra(sesion, uow):
    datos = _escenario(sesion)

    with pytest.raises(TurnoNoEncontrado) as error:
        turno_de_la_agenda(999, datos["usuario"].id, uow)

    assert error.value.referencias[0].recurso_id == 999
