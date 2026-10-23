"""Repositorio del horario sobre SQLAlchemy. Traduce modelos ORM a tipos de dominio (design H2)."""
from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain.agenda.horario import Franja
from app.domain.agenda.profesionales import DatosProfesional
from app.infrastructure.db.modelos import FranjaHorariaModelo, ProfesionalModelo
from app.infrastructure.repositories.consultorio import consultorio_unico


def _profesional_a_dominio(modelo: ProfesionalModelo) -> DatosProfesional:
    return DatosProfesional(
        id=modelo.id, consultorio_id=modelo.consultorio_id, nombre=modelo.nombre, activo=modelo.activo
    )


def _franja_a_dominio(modelo: FranjaHorariaModelo) -> Franja:
    return Franja(
        dia_semana=modelo.dia_semana,
        hora_inicio=modelo.hora_inicio,
        hora_fin=modelo.hora_fin,
        vigente_desde=modelo.vigente_desde,
        vigente_hasta=modelo.vigente_hasta,
    )


class RepositorioHorarioSqlAlchemy:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def consultorio_unico(self) -> int:
        return consultorio_unico(self._sesion)

    def profesionales_del_consultorio(self, consultorio_id: int) -> Sequence[DatosProfesional]:
        consulta = (
            select(ProfesionalModelo)
            .where(ProfesionalModelo.consultorio_id == consultorio_id)
            .order_by(ProfesionalModelo.id)
        )
        return [_profesional_a_dominio(m) for m in self._sesion.scalars(consulta)]

    def profesional(self, profesional_id: int) -> DatosProfesional | None:
        modelo = self._sesion.get(ProfesionalModelo, profesional_id)
        return None if modelo is None else _profesional_a_dominio(modelo)

    def franjas_de(self, profesional_id: int) -> Sequence[Franja]:
        consulta = (
            select(FranjaHorariaModelo)
            .where(FranjaHorariaModelo.profesional_id == profesional_id)
            .order_by(FranjaHorariaModelo.dia_semana, FranjaHorariaModelo.hora_inicio)
        )
        return [_franja_a_dominio(m) for m in self._sesion.scalars(consulta)]

    def reemplazar(self, profesional_id: int, franjas: Sequence[Franja]) -> None:
        self._sesion.execute(
            delete(FranjaHorariaModelo).where(FranjaHorariaModelo.profesional_id == profesional_id)
        )
        self._sesion.add_all(
            FranjaHorariaModelo(
                profesional_id=profesional_id,
                dia_semana=f.dia_semana,
                hora_inicio=f.hora_inicio,
                hora_fin=f.hora_fin,
                vigente_desde=f.vigente_desde,
                vigente_hasta=f.vigente_hasta,
            )
            for f in franjas
        )
        self._sesion.flush()  # el commit es de la unidad de trabajo
