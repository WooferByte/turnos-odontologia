"""Repositorio de la agenda sobre SQLAlchemy. Traduce modelos ORM a tipos de dominio (D12)."""
from collections.abc import Sequence
from dataclasses import replace
from typing import Literal

from sqlalchemy import or_, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.application.puertos import OcupadosEnElIntervalo, SolapamientoEnLaBase
from app.domain.agenda.intervalo import Intervalo
from app.domain.agenda.recursos import Paciente, Prestacion, Profesional, Sillon
from app.domain.agenda.solapamiento import TurnoOcupado
from app.domain.turnos.estados import EstadoTurno
from app.domain.turnos.turno import Turno
from app.infrastructure.db.modelos import (
    ConsultorioModelo,
    PacienteModelo,
    PrestacionModelo,
    ProfesionalModelo,
    SillonModelo,
    TurnoModelo,
)


SQLSTATE_INTERBLOQUEO = "40P01"  # deadlock_detected (design I7)
RECURSO_POR_RESTRICCION: dict[str, Literal["profesional", "sillon"]] = {
    "ex_turno_profesional_sin_solapamiento": "profesional",
    "ex_turno_sillon_sin_solapamiento": "sillon",
}


class RepositorioAgendaSqlAlchemy:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def paciente(self, paciente_id: int) -> Paciente | None:
        modelo = self._sesion.get(PacienteModelo, paciente_id)
        if modelo is None:
            return None
        return Paciente(modelo.id, modelo.consultorio_id)

    def sillon(self, sillon_id: int) -> Sillon | None:
        modelo = self._sesion.get(SillonModelo, sillon_id)
        if modelo is None:
            return None
        return Sillon(modelo.id, modelo.consultorio_id, modelo.activo)

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

    def profesionales_activos(self, consultorio_id: int) -> Sequence[Profesional]:
        consulta = select(ProfesionalModelo).where(
            ProfesionalModelo.consultorio_id == consultorio_id, ProfesionalModelo.activo
        )
        return [
            Profesional(m.id, m.consultorio_id, m.activo) for m in self._sesion.scalars(consulta)
        ]

    def sillones_activos(self, consultorio_id: int) -> Sequence[Sillon]:
        consulta = select(SillonModelo).where(
            SillonModelo.consultorio_id == consultorio_id, SillonModelo.activo
        )
        return [Sillon(m.id, m.consultorio_id, m.activo) for m in self._sesion.scalars(consulta)]

    def zona_horaria(self, consultorio_id: int) -> str:
        return self._sesion.get_one(ConsultorioModelo, consultorio_id).zona_horaria

    def ocupados_en_el_intervalo(
        self, profesional_id: int, sillon_id: int, intervalo: Intervalo
    ) -> OcupadosEnElIntervalo:
        # Una sola sentencia (profesional O sillón) para que ambos recursos se lean del mismo
        # estado de la base (E11, design I8). Recorte por rango para no traer toda la agenda
        # (D12); turnos de cualquier estado: la regla de solapamiento la decide el dominio.
        consulta = select(TurnoModelo).where(
            or_(TurnoModelo.profesional_id == profesional_id, TurnoModelo.sillon_id == sillon_id),
            TurnoModelo.inicio < intervalo.fin,
            TurnoModelo.fin > intervalo.inicio,
        )
        modelos = self._sesion.scalars(consulta).all()

        def ocupado(m: TurnoModelo) -> TurnoOcupado:
            return TurnoOcupado(m.id, Intervalo(m.inicio, m.fin), EstadoTurno(m.estado))

        return OcupadosEnElIntervalo(
            del_profesional=[ocupado(m) for m in modelos if m.profesional_id == profesional_id],
            del_sillon=[ocupado(m) for m in modelos if m.sillon_id == sillon_id],
        )

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
        try:
            self._sesion.flush()  # asigna el id sin confirmar; el commit es de la unidad de trabajo
        except DBAPIError as error:
            # getattr: en SQLite no hay ``diag`` ni ``sqlstate`` y el error sube tal cual (design I7).
            if getattr(error.orig, "sqlstate", None) == SQLSTATE_INTERBLOQUEO:
                # Dos inserciones simultáneas se esperan al comprobar la exclusión y PostgreSQL
                # aborta una: es la misma carrera que 23P01, sin restricción que nombrar.
                raise SolapamientoEnLaBase() from error
            restriccion = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
            recurso = RECURSO_POR_RESTRICCION.get(restriccion)
            if recurso is None:
                raise
            raise SolapamientoEnLaBase(recurso) from error
        return replace(turno, id=modelo.id)
