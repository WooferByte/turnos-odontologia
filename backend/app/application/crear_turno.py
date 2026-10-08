"""Caso de uso: crear un turno (E1). No hace ``commit()`` ni arma SQL: eso es de la unidad de trabajo."""
from dataclasses import dataclass
from datetime import datetime

from app.application.puertos import UnidadDeTrabajo
from app.domain.agenda.intervalo import Intervalo
from app.domain.agenda.recursos import Paciente, Prestacion, Sillon
from app.domain.agenda.solapamiento import detectar_conflictos
from app.domain.errors import (
    EntradaInvalida,
    ErrorDeDominio,
    ErrorDeSolapamiento,
    FechaNoUTC,
    RecursoNoEncontrado,
    ReferenciaInvalida,
)
from app.domain.tiempo import Reloj, exigir_utc, utc_now
from app.domain.turnos.estados import EstadoTurno
from app.domain.turnos.turno import Turno


@dataclass(frozen=True)
class CrearTurnoComando:
    paciente_id: int
    prestacion_id: int
    inicio: datetime
    profesional_id: int | None = None
    sillon_id: int | None = None


def _es_de_otro_consultorio(recurso: Paciente | Prestacion | Sillon,consultorio_id: int | None) -> bool:
    """Un recurso de otro consultorio cuenta como inexistente (D126); sin C no se puede decir."""
    return consultorio_id is not None and recurso.consultorio_id != consultorio_id


def crear_turno(comando: CrearTurnoComando, uow: UnidadDeTrabajo, reloj: Reloj = utc_now) -> Turno:
    with uow:
        # Validación de entrada, toda junta: las dos cosas siempre, sin cortar en la primera (D6).
        errores: list[ErrorDeDominio] = []
        try:
            exigir_utc(comando.inicio, "inicio")
        except FechaNoUTC as error:
            errores.append(error)
        referencias: list[ReferenciaInvalida] = []
        paciente = uow.agenda.paciente(comando.paciente_id)
        if comando.profesional_id is None:  # RN-AG-14: el único activo del consultorio del paciente
            activos = uow.agenda.profesionales_activos(paciente.consultorio_id)
            profesional = activos[0] if len(activos) == 1 else None
        else:
            profesional = uow.agenda.profesional(comando.profesional_id)
        # Consultorio del turno (C, D10): el del profesional; desconocido (None) si no se resolvió.
        consultorio_id = profesional.consultorio_id if profesional and profesional.activo else None
        prestacion = uow.agenda.prestacion(comando.prestacion_id)
        if prestacion is None or _es_de_otro_consultorio(prestacion, consultorio_id):
            referencias.append(ReferenciaInvalida("prestacion", comando.prestacion_id, "inexistente"))
        elif not prestacion.activa:
            referencias.append(ReferenciaInvalida("prestacion", prestacion.id, "inactivo"))
        if paciente is None or _es_de_otro_consultorio(paciente, consultorio_id):
            referencias.append(ReferenciaInvalida("paciente", comando.paciente_id, "inexistente"))
        if profesional is None:
            referencias.append(
                ReferenciaInvalida("profesional", comando.profesional_id, "inexistente")
            )
        elif not profesional.activo:
            referencias.append(ReferenciaInvalida("profesional", profesional.id, "inactivo"))
        if comando.sillon_id is None:  # RN-AG-14: el único activo del consultorio del turno
            activos_sillon = uow.agenda.sillones_activos(consultorio_id)
            sillon = activos_sillon[0] if len(activos_sillon) == 1 else None
        else:
            sillon = uow.agenda.sillon(comando.sillon_id)
        if sillon is None or _es_de_otro_consultorio(sillon, consultorio_id):
            referencias.append(ReferenciaInvalida("sillon", comando.sillon_id, "inexistente"))
        elif not sillon.activo:
            referencias.append(ReferenciaInvalida("sillon", sillon.id, "inactivo"))
        if referencias:
            errores.append(RecursoNoEncontrado(tuple(referencias)))
        if errores:
            raise EntradaInvalida(tuple(errores))
        zona = uow.agenda.zona_horaria(profesional.consultorio_id)
        intervalo = Intervalo.para_turno(comando.inicio, prestacion.duracion_minutos, zona)
        ocupados_profesional = uow.agenda.turnos_que_intersecan(
            "profesional", profesional.id, intervalo
        )
        ocupados_sillon = uow.agenda.turnos_que_intersecan(
            "sillon", comando.sillon_id, intervalo
        )
        conflictos = detectar_conflictos(
            intervalo,
            profesional.id,
            ocupados_profesional,
            sillon.id,
            ocupados_sillon,
        )
        if conflictos:
            raise ErrorDeSolapamiento(conflictos)
        return uow.agenda.agregar(
            Turno(
                consultorio_id=profesional.consultorio_id,
                paciente_id=comando.paciente_id,
                profesional_id=profesional.id,
                sillon_id=sillon.id,
                prestacion_id=prestacion.id,
                inicio=intervalo.inicio,
                fin=intervalo.fin,
                duracion_minutos=prestacion.duracion_minutos,
                estado=EstadoTurno.RESERVADO,
                creado_en=reloj(),
            )
        )
