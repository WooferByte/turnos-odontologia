"""Evento del historial de un turno (RN-AG-11, design H3 y H5). Solo biblioteca estándar."""
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.tiempo import a_texto_utc
from app.domain.turnos.turno import Turno


class TipoEvento(StrEnum):
    CREADO = "creado"


class ActorTipo(StrEnum):
    USUARIO = "usuario"


@dataclass(frozen=True)
class Actor:
    tipo: ActorTipo
    id: str | None = None


@dataclass(frozen=True)
class EventoTurno:
    turno_id: int
    tipo: TipoEvento
    actor_tipo: ActorTipo
    actor_id: str | None
    ocurrido_en: datetime
    antes: dict[str, object] | None
    despues: dict[str, object] | None
    motivo: str | None
    id: int | None = None


def evento_creado(turno: Turno, actor: Actor) -> EventoTurno:
    """El evento ``creado``: la foto del turno al nacer, en el mismo instante de su creación."""
    if turno.id is None:
        raise ValueError("El evento creado cuelga de un turno guardado: el turno no tiene id.")
    return EventoTurno(
        turno_id=turno.id,
        tipo=TipoEvento.CREADO,
        actor_tipo=actor.tipo,
        actor_id=actor.id,
        ocurrido_en=turno.creado_en,
        antes=None,
        despues={
            "estado": turno.estado.value,
            "inicio": a_texto_utc(turno.inicio),
            "fin": a_texto_utc(turno.fin),
            "duracion_minutos": turno.duracion_minutos,
            "paciente_id": turno.paciente_id,
            "prestacion_id": turno.prestacion_id,
            "profesional_id": turno.profesional_id,
            "sillon_id": turno.sillon_id,
        },
        motivo=None,
    )
