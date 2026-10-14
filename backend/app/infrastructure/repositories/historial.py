"""Repositorio del historial sobre SQLAlchemy: solo registra y lee (RN-AG-11, design H7 y H10)."""
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.turnos.eventos import ActorTipo, EventoTurno, TipoEvento
from app.infrastructure.db.modelos import EventoTurnoModelo


def _a_dominio(modelo: EventoTurnoModelo) -> EventoTurno:
    return EventoTurno(
        id=modelo.id,
        turno_id=modelo.turno_id,
        tipo=TipoEvento(modelo.tipo),
        actor_tipo=ActorTipo(modelo.actor_tipo),
        actor_id=modelo.actor_id,
        ocurrido_en=modelo.ocurrido_en,
        antes=modelo.antes,
        despues=modelo.despues,
        motivo=modelo.motivo,
    )


class RepositorioHistorialSqlAlchemy:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def registrar(self, evento: EventoTurno) -> EventoTurno:
        modelo = EventoTurnoModelo(
            turno_id=evento.turno_id,
            tipo=evento.tipo.value,
            actor_tipo=evento.actor_tipo.value,
            actor_id=evento.actor_id,
            ocurrido_en=evento.ocurrido_en,
            antes=evento.antes,
            despues=evento.despues,
            motivo=evento.motivo,
        )
        self._sesion.add(modelo)
        self._sesion.flush()  # asigna el id sin confirmar; el commit es de la unidad de trabajo
        return _a_dominio(modelo)

    def del_turno(self, turno_id: int) -> Sequence[EventoTurno]:
        consulta = (
            select(EventoTurnoModelo)
            .where(EventoTurnoModelo.turno_id == turno_id)
            .order_by(EventoTurnoModelo.ocurrido_en, EventoTurnoModelo.id)
        )
        return [_a_dominio(m) for m in self._sesion.scalars(consulta)]
