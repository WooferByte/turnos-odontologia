"""Casos de uso de lectura de la agenda: los turnos de un día del consultorio y un turno por id (US-011 CA-1).

El consultorio es el del usuario que hace la petición (D270): un turno de otro consultorio cuenta como
inexistente. Solo leen: sin ``commit()``.
"""
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from app.application.puertos import TurnoDeLaAgenda, UnidadDeTrabajo
from app.domain.agenda.dia import hoy_en, rango_del_dia
from app.domain.errors import TurnoNoEncontrado
from app.domain.tiempo import Reloj


@dataclass(frozen=True)
class AgendaDelDia:
    fecha: date
    zona_horaria: str
    turnos: Sequence[TurnoDeLaAgenda]


def agenda_del_dia(fecha: date | None, usuario_id: int, uow: UnidadDeTrabajo, reloj: Reloj) -> AgendaDelDia:
    """Turnos del día ``fecha`` (por defecto, hoy) del consultorio, ordenados por inicio e id."""
    with uow:
        consultorio_id = uow.usuarios.obtener(usuario_id).consultorio_id
        zona = uow.agenda.zona_horaria(consultorio_id)
        dia = fecha if fecha is not None else hoy_en(reloj(), zona)
        desde, hasta = rango_del_dia(dia, zona)
        return AgendaDelDia(dia, zona, uow.agenda.turnos_del_dia(consultorio_id, desde, hasta))


def turno_de_la_agenda(turno_id: int, usuario_id: int, uow: UnidadDeTrabajo) -> TurnoDeLaAgenda:
    with uow:
        consultorio_id = uow.usuarios.obtener(usuario_id).consultorio_id
        turno = uow.agenda.turno_de_la_agenda(turno_id)
        if turno is None or turno.consultorio_id != consultorio_id:
            raise TurnoNoEncontrado(turno_id)
        return turno
