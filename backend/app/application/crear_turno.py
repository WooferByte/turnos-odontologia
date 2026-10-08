"""Caso de uso: crear un turno (E1). No hace ``commit()`` ni arma SQL: eso es de la unidad de trabajo."""
from dataclasses import dataclass
from datetime import datetime

from app.application.puertos import UnidadDeTrabajo
from app.domain.agenda.intervalo import Intervalo
from app.domain.tiempo import Reloj, utc_now
from app.domain.turnos.estados import EstadoTurno
from app.domain.turnos.turno import Turno


@dataclass(frozen=True)
class CrearTurnoComando:
    paciente_id: int
    prestacion_id: int
    inicio: datetime
    profesional_id: int | None = None
    sillon_id: int | None = None


def crear_turno(comando: CrearTurnoComando, uow: UnidadDeTrabajo, reloj: Reloj = utc_now) -> Turno:
    with uow:
        prestacion = uow.agenda.prestacion(comando.prestacion_id)
        profesional = uow.agenda.profesional(comando.profesional_id)
        zona = uow.agenda.zona_horaria(profesional.consultorio_id)
        intervalo = Intervalo.para_turno(comando.inicio, prestacion.duracion_minutos, zona)
        return uow.agenda.agregar(
            Turno(
                consultorio_id=profesional.consultorio_id,
                paciente_id=comando.paciente_id,
                profesional_id=profesional.id,
                sillon_id=comando.sillon_id,
                prestacion_id=prestacion.id,
                inicio=intervalo.inicio,
                fin=intervalo.fin,
                duracion_minutos=prestacion.duracion_minutos,
                estado=EstadoTurno.RESERVADO,
                creado_en=reloj(),
            )
        )
