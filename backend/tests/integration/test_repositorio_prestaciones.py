"""Repositorio de prestaciones sobre SQLite en memoria (US-001 CA-1; RN-AG-15, design P7 y P11)."""
from dataclasses import replace

import pytest
from sqlalchemy.orm import Session

from app.application.puertos import NombreRepetidoEnLaBase
from app.domain.agenda.prestaciones import DatosPrestacion
from app.infrastructure.repositories.prestaciones import RepositorioPrestacionesSqlAlchemy
from tests.factories import un_consultorio


def _nueva(consultorio_id: int, nombre: str = "Blanqueamiento", **kw) -> DatosPrestacion:
    datos = {
        "id": None,
        "consultorio_id": consultorio_id,
        "nombre": nombre,
        "duracion_minutos": 60,
        "color": "#3A7BD5",
        "reservable_online": True,
        "activa": True,
    }
    return DatosPrestacion(**{**datos, **kw})


def test_ca1_agregar_devuelve_la_prestacion_con_id_y_otra_sesion_la_lee(
    sesion: Session, fabrica_sesiones
) -> None:
    consultorio = un_consultorio(sesion)

    with fabrica_sesiones() as escritura:
        guardada = RepositorioPrestacionesSqlAlchemy(escritura).agregar(_nueva(consultorio.id))
        escritura.commit()

    assert guardada.id is not None
    with fabrica_sesiones() as lectura:
        leida = RepositorioPrestacionesSqlAlchemy(lectura).obtener(guardada.id)
    assert leida == DatosPrestacion(
        id=guardada.id,
        consultorio_id=consultorio.id,
        nombre="Blanqueamiento",
        duracion_minutos=60,
        color="#3A7BD5",
        reservable_online=True,
        activa=True,
    )


def test_ca1_del_consultorio_las_trae_por_id_y_no_trae_las_de_otro(sesion: Session) -> None:
    uno = un_consultorio(sesion)
    otro = un_consultorio(sesion)
    repositorio = RepositorioPrestacionesSqlAlchemy(sesion)
    segunda = repositorio.agregar(_nueva(uno.id, "Limpieza"))
    primera = repositorio.agregar(_nueva(uno.id, "Control"))
    repositorio.agregar(_nueva(otro.id, "Extracción"))

    del_uno = repositorio.del_consultorio(uno.id)

    assert [p.id for p in del_uno] == sorted([primera.id, segunda.id])
    assert {p.nombre for p in del_uno} == {"Limpieza", "Control"}


def test_ca1_obtener_una_prestacion_inexistente_devuelve_none(sesion: Session) -> None:
    assert RepositorioPrestacionesSqlAlchemy(sesion).obtener(999) is None


def test_ca1_guardar_actualiza_solo_esa_fila(sesion: Session) -> None:
    consultorio = un_consultorio(sesion)
    repositorio = RepositorioPrestacionesSqlAlchemy(sesion)
    a_editar = repositorio.agregar(_nueva(consultorio.id, "Limpieza"))
    intacta = repositorio.agregar(_nueva(consultorio.id, "Control"))

    devuelta = repositorio.guardar(
        replace(a_editar, duracion_minutos=45, color="#43A047", reservable_online=False, activa=False)
    )

    assert devuelta.duracion_minutos == 45
    leida = repositorio.obtener(a_editar.id)
    assert (leida.duracion_minutos, leida.color, leida.reservable_online, leida.activa) == (
        45,
        "#43A047",
        False,
        False,
    )
    assert repositorio.obtener(intacta.id) == intacta


def test_ca1_consultorio_unico_devuelve_el_id_del_unico_consultorio(sesion: Session) -> None:
    consultorio = un_consultorio(sesion)

    assert RepositorioPrestacionesSqlAlchemy(sesion).consultorio_unico() == consultorio.id


def test_ca1_agregar_con_el_mismo_nombre_exacto_levanta_nombre_repetido_en_la_base(
    sesion: Session,
) -> None:
    consultorio = un_consultorio(sesion)
    repositorio = RepositorioPrestacionesSqlAlchemy(sesion)
    repositorio.agregar(_nueva(consultorio.id, "Limpieza"))

    with pytest.raises(NombreRepetidoEnLaBase):
        repositorio.agregar(_nueva(consultorio.id, "Limpieza"))


def test_ca1_la_unidad_de_trabajo_expone_prestaciones_sobre_la_misma_sesion_que_agenda(
    sesion: Session, uow
) -> None:
    consultorio = un_consultorio(sesion)

    with uow:
        guardada = uow.prestaciones.agregar(_nueva(consultorio.id))
        vista_por_la_agenda = uow.agenda.prestacion(guardada.id)  # sin commit: misma sesión

    assert vista_por_la_agenda is not None
    assert vista_por_la_agenda.duracion_minutos == 60
