"""Repositorio de la agenda sobre SQLAlchemy. Traduce modelos ORM a tipos de dominio (D12)."""
from collections.abc import Sequence
from dataclasses import replace
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.agenda.intervalo import Intervalo
from app.domain.agenda.recursos import Prestacion, Profesional
from app.domain.agenda.solapamiento import TurnoOcupado
from app.domain.turnos.estados import EstadoTurno
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

    def turnos_que_intersecan(
        self, recurso: Literal["profesional", "sillon"], recurso_id: int, intervalo: Intervalo
    ) -> Sequence[TurnoOcupado]:
        # Por ahora devuelve todos los turnos del recurso: el recorte por rango
        # (inicio < fin pedido AND fin > inicio pedido) entra en el grupo 9 (tarea 9.3).
        columna = TurnoModelo.profesional_id if recurso == "profesional" else TurnoModelo.sillon_id
        modelos = self._sesion.scalars(select(TurnoModelo).where(columna == recurso_id)).all()
        return [
            TurnoOcupado(m.id, Intervalo(m.inicio, m.fin), EstadoTurno(m.estado)) for m in modelos
        ]

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
