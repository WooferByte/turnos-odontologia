"""Casos de uso de sillones sobre SQLite en memoria (US-004 CA-3; RN-AG-06, RN-GL-04)."""
import pytest

from app.application.sillones import (
    CrearSillonComando,
    EditarSillonComando,
    crear_sillon,
    editar_sillon,
    listar_sillones,
)
from app.domain.errors import SillonNoEncontrado
from tests.factories import un_consultorio, un_sillon


def test_ca3_crear_sillon_lo_guarda_activo(sesion, uow) -> None:
    consultorio = un_consultorio(sesion)

    creado = crear_sillon(CrearSillonComando(nombre="Sillón 2"), uow)

    assert creado.id is not None
    assert (creado.nombre, creado.activo, creado.consultorio_id) == ("Sillón 2", True, consultorio.id)
    assert listar_sillones(uow) == [creado]  # confirmado: otra sesión lo ve


def test_ca3_listar_sillones_incluye_los_inactivos(sesion, uow) -> None:
    consultorio = un_consultorio(sesion)
    activo = un_sillon(sesion, consultorio, nombre="Sillón 1")
    inactivo = un_sillon(sesion, consultorio, nombre="Sillón 2", activo=False)

    listados = listar_sillones(uow)

    assert [(s.id, s.nombre, s.activo) for s in listados] == [
        (activo.id, "Sillón 1", True),
        (inactivo.id, "Sillón 2", False),
    ]


def test_ca3_editar_sillon_inexistente_rechaza_con_rn_gl_04(sesion, uow) -> None:
    un_consultorio(sesion)

    with pytest.raises(SillonNoEncontrado) as excinfo:
        editar_sillon(999, EditarSillonComando(nombre="Box"), uow)

    assert excinfo.value.codigos == ["RN-GL-04"]
    (referencia,) = excinfo.value.referencias
    assert (referencia.recurso, referencia.recurso_id, referencia.motivo) == (
        "sillon",
        999,
        "inexistente",
    )
