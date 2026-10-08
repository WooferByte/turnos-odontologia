"""Puertos que la capa de aplicación necesita; los implementa ``infrastructure`` (D12)."""
from collections.abc import Sequence
from typing import Literal, Protocol

from app.domain.agenda.intervalo import Intervalo
from app.domain.agenda.recursos import Paciente, Prestacion, Profesional, Sillon
from app.domain.agenda.solapamiento import TurnoOcupado
from app.domain.turnos.turno import Turno


class RepositorioAgenda(Protocol):
    def paciente(self, paciente_id: int) -> Paciente | None: ...

    def prestacion(self, prestacion_id: int) -> Prestacion | None: ...

    def sillon(self, sillon_id: int) -> Sillon | None: ...

    def profesional(self, profesional_id: int) -> Profesional | None: ...

    def profesionales_activos(self, consultorio_id: int) -> Sequence[Profesional]: ...

    def sillones_activos(self, consultorio_id: int) -> Sequence[Sillon]: ...

    def zona_horaria(self, consultorio_id: int) -> str: ...

    def turnos_que_intersecan(
        self, recurso: Literal["profesional", "sillon"], recurso_id: int, intervalo: Intervalo
    ) -> Sequence[TurnoOcupado]:
        """Turnos del recurso en cualquier estado; la regla la decide el dominio (D12)."""
        ...

    def agregar(self, turno: Turno) -> Turno:
        """Guarda el turno y lo devuelve con su id."""
        ...


class UnidadDeTrabajo(Protocol):
    agenda: RepositorioAgenda

    def __enter__(self) -> "UnidadDeTrabajo": ...

    def __exit__(self, tipo, valor, traza) -> None: ...
