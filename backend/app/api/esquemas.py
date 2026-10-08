"""Esquemas HTTP de ``POST /turnos`` (D4). Es la única capa que conoce Pydantic."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.turnos.turno import Turno


class CrearTurnoEntrada(BaseModel):
    """Cuerpo de la petición. No valida la zona de ``inicio``: eso es del caso de uso (D6)."""

    model_config = ConfigDict(extra="forbid")

    paciente_id: int
    prestacion_id: int
    inicio: datetime
    profesional_id: int | None = None
    sillon_id: int | None = None


class TurnoSalida(BaseModel):
    """Respuesta ``201``: los once campos del turno creado."""

    id: int
    consultorio_id: int
    paciente_id: int
    profesional_id: int
    sillon_id: int
    prestacion_id: int
    inicio: datetime
    fin: datetime
    duracion_minutos: int
    estado: str
    creado_en: datetime

    @classmethod
    def desde_turno(cls, turno: Turno) -> "TurnoSalida":
        return cls(
            id=turno.id,
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
