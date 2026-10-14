"""Repositorio de sillones sobre SQLite en memoria (US-004 CA-3, CA-2; RN-AG-06, design S9)."""
from dataclasses import replace

from sqlalchemy.orm import Session

from app.domain.agenda.sillones import DatosSillon
from app.infrastructure.repositories.sillones import RepositorioSillonesSqlAlchemy
from tests.factories import un_consultorio, un_sillon


def _nuevo(consultorio_id: int, nombre: str = "Sillón 2", activo: bool = True) -> DatosSillon:
    return DatosSillon(id=None, consultorio_id=consultorio_id, nombre=nombre, activo=activo)


def test_ca3_agregar_devuelve_el_sillon_con_id_y_otra_sesion_lo_lee(
    sesion: Session, fabrica_sesiones
) -> None:
    consultorio = un_consultorio(sesion)

    with fabrica_sesiones() as escritura:
        guardado = RepositorioSillonesSqlAlchemy(escritura).agregar(_nuevo(consultorio.id))
        escritura.commit()

    assert guardado.id is not None
    with fabrica_sesiones() as lectura:
        leido = RepositorioSillonesSqlAlchemy(lectura).obtener(guardado.id)
    assert leido == DatosSillon(
        id=guardado.id, consultorio_id=consultorio.id, nombre="Sillón 2", activo=True
    )


def test_ca3_del_consultorio_los_trae_por_id_con_inactivos_y_sin_los_de_otro(
    sesion: Session,
) -> None:
    uno = un_consultorio(sesion)
    otro = un_consultorio(sesion)
    primero = un_sillon(sesion, uno, nombre="Sillón A")
    segundo = un_sillon(sesion, uno, nombre="Sillón B", activo=False)
    un_sillon(sesion, otro, nombre="Sillón ajeno")

    traidos = RepositorioSillonesSqlAlchemy(sesion).del_consultorio(uno.id)

    assert [(s.id, s.nombre, s.activo) for s in traidos] == [
        (primero.id, "Sillón A", True),
        (segundo.id, "Sillón B", False),
    ]


def test_ca3_obtener_un_id_inexistente_da_none(sesion: Session) -> None:
    assert RepositorioSillonesSqlAlchemy(sesion).obtener(999) is None


def test_ca3_guardar_actualiza_solo_esa_fila(sesion: Session, fabrica_sesiones) -> None:
    consultorio = un_consultorio(sesion)
    editado = un_sillon(sesion, consultorio, nombre="Sillón A")
    intacto = un_sillon(sesion, consultorio, nombre="Sillón B")

    with fabrica_sesiones() as escritura:
        repositorio = RepositorioSillonesSqlAlchemy(escritura)
        guardado = repositorio.guardar(
            replace(repositorio.obtener(editado.id), nombre="Box de cirugía", activo=False)
        )
        escritura.commit()

    assert guardado.nombre == "Box de cirugía"
    with fabrica_sesiones() as lectura:
        repositorio = RepositorioSillonesSqlAlchemy(lectura)
        assert repositorio.obtener(editado.id) == DatosSillon(
            id=editado.id, consultorio_id=consultorio.id, nombre="Box de cirugía", activo=False
        )
        assert repositorio.obtener(intacto.id) == DatosSillon(
            id=intacto.id, consultorio_id=consultorio.id, nombre="Sillón B", activo=True
        )


def test_ca3_consultorio_unico_devuelve_el_id_del_unico_consultorio(sesion: Session) -> None:
    consultorio = un_consultorio(sesion)

    assert RepositorioSillonesSqlAlchemy(sesion).consultorio_unico() == consultorio.id


def test_ca2_la_unidad_de_trabajo_expone_sillones_sobre_la_misma_sesion_que_agenda(
    sesion: Session, uow
) -> None:
    consultorio = un_consultorio(sesion)

    with uow:
        agregado = uow.sillones.agregar(_nuevo(consultorio.id))
        activos = uow.agenda.sillones_activos(consultorio.id)

    assert [s.id for s in activos] == [agregado.id]
