"""Casos de uso del catálogo de sillones (US-004 CA-3; RN-AG-06, RN-AG-07, RN-GL-04). Sin ``commit()`` ni SQL."""
from collections.abc import Sequence
from dataclasses import dataclass, replace

from app.application.puertos import UnidadDeTrabajo
from app.domain.agenda.sillones import DatosSillon
from app.domain.errors import SillonNoEncontrado


@dataclass(frozen=True)
class CrearSillonComando:
    nombre: str


@dataclass(frozen=True)
class EditarSillonComando:
    """Un campo en ``None`` significa «no cambia»: el ``null`` explícito ya lo rechazó la API (S7)."""

    nombre: str | None = None
    activo: bool | None = None


def listar_sillones(uow: UnidadDeTrabajo) -> Sequence[DatosSillon]:
    """Todos los del consultorio, activos e inactivos, por ``id``."""
    with uow:
        return uow.sillones.del_consultorio(uow.sillones.consultorio_unico())


def crear_sillon(comando: CrearSillonComando, uow: UnidadDeTrabajo) -> DatosSillon:
    with uow:
        nuevo = DatosSillon(
            id=None,
            consultorio_id=uow.sillones.consultorio_unico(),
            nombre=comando.nombre,
            activo=True,
        )
        return uow.sillones.agregar(nuevo)


def editar_sillon(
    sillon_id: int, comando: EditarSillonComando, uow: UnidadDeTrabajo
) -> DatosSillon:
    with uow:
        actual = uow.sillones.obtener(sillon_id)
        if actual is None:
            raise SillonNoEncontrado(sillon_id)
        cambios = {campo: valor for campo, valor in vars(comando).items() if valor is not None}
        return uow.sillones.guardar(replace(actual, **cambios))
