"""Repositorio de la agenda sobre SQLAlchemy. Traduce modelos ORM a tipos de dominio (D12)."""
from dataclasses import replace

from sqlalchemy.orm import Session

from app.domain.agenda.recursos import Prestacion, Profesional
from app.domain.turnos.turno import Turno
from app.infrastructure.db.modelos import (
    ConsultorioModelo,
    PrestacionModelo,
    ProfesionalModelo,
    TurnoModelo,
)


class RepositorioAgendaSqlAlchemy:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def prestacion(self, prestacion_id: int) -> Prestacion | None:
        modelo = self._sesion.get(PrestacionModelo, prestacion_id)
        if modelo is None:
            return None
        return Prestacion(modelo.id, modelo.consultorio_id, modelo.duracion_minutos, modelo.activa)

    def profesional(self, profesional_id: int) -> Profesional | None:
        modelo = self._sesion.get(ProfesionalModelo, profesional_id)
        if modelo is None:
            return None
        return Profesional(modelo.id, modelo.consultorio_id, modelo.activo)

    def zona_horaria(self, consultorio_id: int) -> str:
        return self._sesion.get_one(ConsultorioModelo, consultorio_id).zona_horaria

    def agregar(self, turno: Turno) -> Turno:
        modelo = TurnoModelo(
            consultorio_id=turno.consultorio_id,
            paciente_id=turno.paciente_id,
            profesional_id=turno.profesional_id,
            sillon_id=turno.sillon_id,
            prestacion_id=turno.prestacion_id,
            inicio=turno.inicio,
            fin=turno.fin,
            duracion_minutos=turno.duracion_minutos,
            estado=turno.estado.value,
            creado_en=turno.creado_en,
        )
        self._sesion.add(modelo)
        self._sesion.flush()  # asigna el id sin confirmar; el commit es de la unidad de trabajo
        return replace(turno, id=modelo.id)
