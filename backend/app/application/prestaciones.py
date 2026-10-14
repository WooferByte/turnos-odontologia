"""Casos de uso del catálogo de prestaciones (US-001 CA-1 y CA-2; RN-AG-01, RN-AG-15, RN-GL-04). Sin ``commit()`` ni SQL."""
from collections.abc import Sequence
from dataclasses import dataclass, replace

from app.application.puertos import NombreRepetidoEnLaBase, UnidadDeTrabajo
from app.domain.agenda.prestaciones import (
    GRANULARIDAD_MINUTOS,
    DatosPrestacion,
    duracion_valida,
    nombre_repetido,
)
from app.domain.errors import (
    DuracionInvalida,
    EntradaInvalida,
    NombreDePrestacionRepetido,
    PrestacionNoEncontrada,
)


@dataclass(frozen=True)
class CrearPrestacionComando:
    nombre: str
    duracion_minutos: int
    color: str
    reservable_online: bool = False


@dataclass(frozen=True)
class EditarPrestacionComando:
    """Un campo en ``None`` significa «no cambia»: el ``null`` explícito ya lo rechazó la API (P9)."""

    nombre: str | None = None
    duracion_minutos: int | None = None
    color: str | None = None
    reservable_online: bool | None = None
    activa: bool | None = None


def _validar_duracion(minutos: int) -> None:
    """RN-AG-01 es validación de entrada: viaja dentro de un ``EntradaInvalida`` (design P8)."""
    if not duracion_valida(minutos):
        raise EntradaInvalida((DuracionInvalida(GRANULARIDAD_MINUTOS),))


def listar_prestaciones(uow: UnidadDeTrabajo) -> Sequence[DatosPrestacion]:
    """Todas las del consultorio, activas e inactivas, por ``id``."""
    with uow:
        return uow.prestaciones.del_consultorio(uow.prestaciones.consultorio_unico())


def crear_prestacion(comando: CrearPrestacionComando, uow: UnidadDeTrabajo) -> DatosPrestacion:
    with uow:
        _validar_duracion(comando.duracion_minutos)
        consultorio_id = uow.prestaciones.consultorio_unico()
        existente = nombre_repetido(comando.nombre, uow.prestaciones.del_consultorio(consultorio_id))
        if existente is not None:
            raise NombreDePrestacionRepetido(existente.nombre)
        nueva = DatosPrestacion(
            id=None,
            consultorio_id=consultorio_id,
            nombre=comando.nombre,
            duracion_minutos=comando.duracion_minutos,
            color=comando.color,
            reservable_online=comando.reservable_online,
            activa=True,
        )
        try:
            return uow.prestaciones.agregar(nueva)
        except NombreRepetidoEnLaBase as error:
            # Carrera de dos altas idénticas: la base ya tiene ese nombre exacto (design P7).
            raise NombreDePrestacionRepetido(comando.nombre) from error


def editar_prestacion(
    prestacion_id: int, comando: EditarPrestacionComando, uow: UnidadDeTrabajo
) -> DatosPrestacion:
    with uow:
        actual = uow.prestaciones.obtener(prestacion_id)
        if actual is None:
            raise PrestacionNoEncontrada(prestacion_id)
        if comando.duracion_minutos is not None:
            _validar_duracion(comando.duracion_minutos)
        if comando.nombre is not None:
            otras = uow.prestaciones.del_consultorio(actual.consultorio_id)
            existente = nombre_repetido(comando.nombre, otras, excepto_id=actual.id)
            if existente is not None:
                raise NombreDePrestacionRepetido(existente.nombre)
        cambios = {campo: valor for campo, valor in vars(comando).items() if valor is not None}
        try:
            return uow.prestaciones.guardar(replace(actual, **cambios))
        except NombreRepetidoEnLaBase as error:
            raise NombreDePrestacionRepetido(comando.nombre or actual.nombre) from error
