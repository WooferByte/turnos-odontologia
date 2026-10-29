"""Repositorio de la agenda sobre SQLAlchemy. Traduce modelos ORM a tipos de dominio (D12)."""
from collections.abc import Sequence
from datetime import datetime
from dataclasses import replace
from typing import Literal

from sqlalchemy import or_, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.application.puertos import OcupadosEnElIntervalo, SolapamientoEnLaBase, TurnoDeLaAgenda
from app.domain.agenda.bloqueos import Alcance, DatosBloqueo
from app.domain.agenda.intervalo import Intervalo
from app.domain.agenda.recursos import Paciente, Prestacion, Profesional, Sillon
from app.domain.agenda.solapamiento import TurnoOcupado
from app.domain.turnos.estados import ESTADOS_ACTIVOS, EstadoTurno
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


def _turno_a_dominio(modelo: TurnoModelo) -> Turno:
    return Turno(
        id=modelo.id,
        consultorio_id=modelo.consultorio_id,
        paciente_id=modelo.paciente_id,
        profesional_id=modelo.profesional_id,
        sillon_id=modelo.sillon_id,
        prestacion_id=modelo.prestacion_id,
        inicio=modelo.inicio,
        fin=modelo.fin,
        duracion_minutos=modelo.duracion_minutos,
        estado=EstadoTurno(modelo.estado),
        creado_en=modelo.creado_en,
        creado_por=modelo.creado_por,
    )


def _turno_de_la_agenda(turno: TurnoModelo, paciente: PacienteModelo, prestacion: PrestacionModelo) -> TurnoDeLaAgenda:
    return TurnoDeLaAgenda(
        id=turno.id,
        consultorio_id=turno.consultorio_id,
        inicio=turno.inicio,
        fin=turno.fin,
        duracion_minutos=turno.duracion_minutos,
        estado=turno.estado,
        profesional_id=turno.profesional_id,
        sillon_id=turno.sillon_id,
        paciente_id=paciente.id,
        paciente_nombre=paciente.nombre,
        paciente_apellido=paciente.apellido,
        prestacion_id=prestacion.id,
        prestacion_nombre=prestacion.nombre,
        prestacion_color=prestacion.color,
    )


def _consulta_de_la_agenda():
    # Una sola consulta con join: sin N+1 y sin traer del paciente más que nombre y apellido (D318).
    return select(TurnoModelo, PacienteModelo, PrestacionModelo).join(
        PacienteModelo, PacienteModelo.id == TurnoModelo.paciente_id
    ).join(PrestacionModelo, PrestacionModelo.id == TurnoModelo.prestacion_id)


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

    def bloquear_recursos(self, profesional_id: int, sillon_id: int) -> None:
        # Dos sentencias, siempre en este orden (primero el profesional): con el orden fijo dos
        # reservas con recursos cruzados no se interbloquean (E11, design I8). key_share=True
        # emite FOR NO KEY UPDATE en PostgreSQL: se excluye con otro igual, pero no frena un
        # INSERT que solo referencia la fila por clave foránea. SQLite omite la cláusula.
        self._sesion.execute(
            select(ProfesionalModelo.id)
            .where(ProfesionalModelo.id == profesional_id)
            .with_for_update(key_share=True)
        )
        self._sesion.execute(
            select(SillonModelo.id)
            .where(SillonModelo.id == sillon_id)
            .with_for_update(key_share=True)
        )

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

    def _volcar_traduciendo_choques(self) -> None:
        try:
            self._sesion.flush()
        except DBAPIError as error:
            # getattr: en SQLite no hay ``diag`` ni ``sqlstate`` y el error sube tal cual (design I7).
            if getattr(error.orig, "sqlstate", None) == SQLSTATE_INTERBLOQUEO:
                # Dos escrituras simultáneas se esperan al comprobar la exclusión y PostgreSQL
                # aborta una: es la misma carrera que 23P01, sin restricción que nombrar.
                raise SolapamientoEnLaBase() from error
            restriccion = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
            recurso = RECURSO_POR_RESTRICCION.get(restriccion)
            if recurso is None:
                raise
            raise SolapamientoEnLaBase(recurso) from error

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
            creado_por=turno.creado_por,
        )
        self._sesion.add(modelo)
        self._volcar_traduciendo_choques()  # asigna el id sin confirmar; el commit es de la unidad de trabajo
        return replace(turno, id=modelo.id)

    def turno_para_cambiar(self, turno_id: int) -> Turno | None:
        consulta = select(TurnoModelo).where(TurnoModelo.id == turno_id).with_for_update(key_share=True)
        modelo = self._sesion.scalars(consulta).first()
        return None if modelo is None else _turno_a_dominio(modelo)

    def reprogramar(self, turno_id: int, inicio: datetime, fin: datetime, duracion_minutos: int) -> Turno:
        modelo = self._sesion.get_one(TurnoModelo, turno_id)
        modelo.inicio = inicio
        modelo.fin = fin
        modelo.duracion_minutos = duracion_minutos
        self._volcar_traduciendo_choques()
        return _turno_a_dominio(modelo)

    def cambiar_estado(self, turno_id: int, estado: EstadoTurno) -> Turno:
        modelo = self._sesion.get_one(TurnoModelo, turno_id)
        modelo.estado = estado.value
        self._sesion.flush()  # cancelar solo libera el horario: no puede violar la exclusión (X5)
        return _turno_a_dominio(modelo)

    def existe_turno(self, turno_id: int) -> bool:
        return self._sesion.get(TurnoModelo, turno_id) is not None

    def turnos_activos_que_intersecan(self, bloqueo: DatosBloqueo) -> Sequence[Turno]:
        consulta = select(TurnoModelo).where(
            TurnoModelo.consultorio_id == bloqueo.consultorio_id,
            TurnoModelo.estado.in_([estado.value for estado in ESTADOS_ACTIVOS]),
            TurnoModelo.inicio < bloqueo.fin,
            TurnoModelo.fin > bloqueo.inicio,
        )
        if bloqueo.alcance is Alcance.PROFESIONAL:
            consulta = consulta.where(TurnoModelo.profesional_id == bloqueo.profesional_id)
        elif bloqueo.alcance is Alcance.SILLON:
            consulta = consulta.where(TurnoModelo.sillon_id == bloqueo.sillon_id)
        consulta = consulta.order_by(TurnoModelo.inicio, TurnoModelo.id)
        return [_turno_a_dominio(m) for m in self._sesion.scalars(consulta)]

    def turnos_del_dia(
        self, consultorio_id: int, desde: datetime, hasta: datetime
    ) -> Sequence[TurnoDeLaAgenda]:
        consulta = (
            _consulta_de_la_agenda()
            .where(
                TurnoModelo.consultorio_id == consultorio_id,
                TurnoModelo.inicio >= desde,
                TurnoModelo.inicio < hasta,
            )
            .order_by(TurnoModelo.inicio, TurnoModelo.id)
        )
        return [_turno_de_la_agenda(*fila) for fila in self._sesion.execute(consulta)]

    def turno_de_la_agenda(self, turno_id: int) -> TurnoDeLaAgenda | None:
        fila = self._sesion.execute(_consulta_de_la_agenda().where(TurnoModelo.id == turno_id)).first()
        return None if fila is None else _turno_de_la_agenda(*fila)
