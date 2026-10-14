"""Casos de uso de prestaciones sobre SQLite en memoria (US-001 CA-1; RN-AG-15, RN-GL-04)."""
import pytest

from app.application.prestaciones import (
    CrearPrestacionComando,
    crear_prestacion,
    listar_prestaciones,
)
from app.domain.errors import NombreDePrestacionRepetido
from tests.factories import un_consultorio, una_prestacion


def _alta(nombre: str = "Blanqueamiento", **kw) -> CrearPrestacionComando:
    datos = {"nombre": nombre, "duracion_minutos": 60, "color": "#3A7BD5"}
    return CrearPrestacionComando(**{**datos, **kw})


def test_ca1_crear_prestacion_la_guarda_activa_y_no_reservable(sesion, uow) -> None:
    un_consultorio(sesion)

    creada = crear_prestacion(_alta(), uow)

    assert creada.id is not None
    assert (creada.nombre, creada.duracion_minutos, creada.color) == ("Blanqueamiento", 60, "#3A7BD5")
    assert creada.activa is True
    assert creada.reservable_online is False
    assert listar_prestaciones(uow) == [creada]  # confirmada: otra sesión la ve


def test_ca1_listar_prestaciones_incluye_las_inactivas(sesion, uow) -> None:
    consultorio = un_consultorio(sesion)
    activa = una_prestacion(sesion, consultorio, nombre="Limpieza")
    inactiva = una_prestacion(sesion, consultorio, nombre="Obturación", activa=False)

    listadas = listar_prestaciones(uow)

    assert [(p.id, p.nombre, p.activa) for p in listadas] == [
        (activa.id, "Limpieza", True),
        (inactiva.id, "Obturación", False),
    ]


def test_ca1_nombre_repetido_rechaza_con_rn_ag_15(sesion, uow) -> None:
    consultorio = un_consultorio(sesion)
    una_prestacion(sesion, consultorio, nombre="Limpieza")

    with pytest.raises(NombreDePrestacionRepetido) as excinfo:
        crear_prestacion(_alta("Limpieza"), uow)

    assert excinfo.value.codigos == ["RN-AG-15"]
    assert [p.nombre for p in listar_prestaciones(uow)] == ["Limpieza"]
