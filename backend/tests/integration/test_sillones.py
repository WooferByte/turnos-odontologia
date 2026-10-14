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
from app.infrastructure.db.modelos import TurnoModelo
from tests.conftest import a_las
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
)


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


def test_ca3_renombrar_cambia_solo_el_nombre(sesion, uow) -> None:
    consultorio = un_consultorio(sesion)
    sillon = un_sillon(sesion, consultorio, nombre="Sillón 1", activo=False)

    editado = editar_sillon(sillon.id, EditarSillonComando(nombre="Box de cirugía"), uow)

    assert (editado.id, editado.nombre, editado.activo) == (sillon.id, "Box de cirugía", False)
    assert listar_sillones(uow) == [editado]


@pytest.mark.parametrize("activo", [False, True])
def test_ca3_desactivar_y_reactivar(sesion, uow, activo: bool) -> None:
    consultorio = un_consultorio(sesion)
    sillon = un_sillon(sesion, consultorio, nombre="Sillón 1", activo=not activo)

    editado = editar_sillon(sillon.id, EditarSillonComando(activo=activo), uow)

    assert (editado.nombre, editado.activo) == ("Sillón 1", activo)
    assert [s.activo for s in listar_sillones(uow)] == [activo]  # sigue listado


def test_ca3_edicion_sin_campos_no_cambia_nada(sesion, uow) -> None:
    consultorio = un_consultorio(sesion)
    sillon = un_sillon(sesion, consultorio, nombre="Sillón 1")

    editado = editar_sillon(sillon.id, EditarSillonComando(), uow)

    assert (editado.id, editado.nombre, editado.activo) == (sillon.id, "Sillón 1", True)


def test_ca3_desactivar_no_modifica_los_turnos_del_sillon(sesion, uow, fabrica_sesiones) -> None:
    consultorio = un_consultorio(sesion)
    sillon = un_sillon(sesion, consultorio)
    turno = un_turno(
        sesion,
        paciente=un_paciente(sesion, consultorio),
        profesional=un_profesional(sesion, consultorio),
        sillon=sillon,
        prestacion=una_prestacion(sesion, consultorio),
        inicio=a_las(10),
    )

    editar_sillon(sillon.id, EditarSillonComando(activo=False), uow)

    with fabrica_sesiones() as otra:
        guardado = otra.get(TurnoModelo, turno.id)
        assert (guardado.estado, guardado.inicio, guardado.fin, guardado.sillon_id) == (
            "reservado",
            a_las(10),
            a_las(10, 30),
            sillon.id,
        )
