"""Puertos que la capa de aplicación necesita; los implementa ``infrastructure`` (D12)."""
from typing import Protocol

from app.domain.agenda.recursos import Prestacion, Profesional
from app.domain.turnos.turno import Turno


class RepositorioAgenda(Protocol):
    def prestacion(self, prestacion_id: int) -> Prestacion | None: ...

    def profesional(self, profesional_id: int) -> Profesional | None: ...

    def zona_horaria(self, consultorio_id: int) -> str: ...

    def agregar(self, turno: Turno) -> Turno:
        """Guarda el turno y lo devuelve con su id."""
        ...


class UnidadDeTrabajo(Protocol):
    agenda: RepositorioAgenda

    def __enter__(self) -> "UnidadDeTrabajo": ...

    def __exit__(self, tipo, valor, traza) -> None: ...
