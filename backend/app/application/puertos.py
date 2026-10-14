"""Puertos que la capa de aplicación necesita; los implementa ``infrastructure`` (D12)."""
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

from app.domain.agenda.intervalo import Intervalo
from app.domain.agenda.recursos import Paciente, Prestacion, Profesional, Sillon
from app.domain.agenda.solapamiento import TurnoOcupado
from app.domain.turnos.eventos import EventoTurno
from app.domain.turnos.turno import Turno


@dataclass(frozen=True)
class OcupadosEnElIntervalo:
    """Los turnos que intersecan un intervalo, separados por el recurso con el que chocan."""

    del_profesional: Sequence[TurnoOcupado]
    del_sillon: Sequence[TurnoOcupado]


class RepositorioAgenda(Protocol):
    def paciente(self, paciente_id: int) -> Paciente | None: ...

    def prestacion(self, prestacion_id: int) -> Prestacion | None: ...

    def sillon(self, sillon_id: int) -> Sillon | None: ...

    def profesional(self, profesional_id: int) -> Profesional | None: ...

    def profesionales_activos(self, consultorio_id: int) -> Sequence[Profesional]: ...

    def sillones_activos(self, consultorio_id: int) -> Sequence[Sillon]: ...

    def zona_horaria(self, consultorio_id: int) -> str: ...

    def bloquear_recursos(self, profesional_id: int, sillon_id: int) -> None:
        """Toma, hasta que termine la transacción, el bloqueo del profesional y después el del sillón.

        Serializa las reservas del mismo recurso: la segunda espera, y al continuar lee el turno
        que la primera ya confirmó (E11, design I8). El orden es siempre el mismo: así dos
        reservas con recursos cruzados no se interbloquean entre sí.
        """
        ...

    def ocupados_en_el_intervalo(
        self, profesional_id: int, sillon_id: int, intervalo: Intervalo
    ) -> "OcupadosEnElIntervalo":
        """Turnos del profesional y del sillón en cualquier estado, leídos con UNA sentencia.

        La regla la decide el dominio (D12). Una sola lectura evita que una reserva confirmada
        entre dos consultas deje ver un solo choque donde hay dos (E11, design I8).
        """
        ...

    def agregar(self, turno: Turno) -> Turno:
        """Guarda el turno y lo devuelve con su id."""
        ...

    def existe_turno(self, turno_id: int) -> bool: ...


class RepositorioHistorial(Protocol):
    """Historial de solo inserción: registrar y leer, nada más (RN-AG-11, design H7)."""

    def registrar(self, evento: EventoTurno) -> EventoTurno:
        """Guarda el evento y lo devuelve con su id."""
        ...

    def del_turno(self, turno_id: int) -> Sequence[EventoTurno]:
        """Los eventos del turno, por ``ocurrido_en`` y, a igual momento, por orden de registro."""
        ...


class UnidadDeTrabajo(Protocol):
    agenda: RepositorioAgenda
    historial: RepositorioHistorial

    def __enter__(self) -> "UnidadDeTrabajo": ...

    def __exit__(self, tipo, valor, traza) -> None: ...


class SolapamientoEnLaBase(Exception):
    """La base rechazó el alta porque otra transacción ocupó el hueco (RN-AG-10c, design I7).

    No es un error de dominio ni lleva código RN: el caso de uso la reevalúa con el dominio.
    recurso dice qué recurso chocó cuando la base lo informa (rechazo de la restricción de
    exclusión, 23P01); es None cuando no hay dato fiable, como en un interbloqueo (40P01):
    ahí PostgreSQL aborta una de dos transacciones que se esperan y no nombra ninguna restricción.
    """

    def __init__(self, recurso: Literal["profesional", "sillon"] | None = None) -> None:
        self.recurso = recurso
        detalle = f" del {recurso}" if recurso else ""
        super().__init__(f"La base rechazó el turno por solapamiento{detalle}.")
