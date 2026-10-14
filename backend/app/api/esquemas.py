"""Esquemas HTTP de ``/turnos`` (D4) y ``/prestaciones`` (C-04). Es la única capa que conoce Pydantic."""
from datetime import datetime
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator

from app.domain.agenda.nombres import normalizar_espacios
from app.domain.agenda.prestaciones import DatosPrestacion
from app.domain.turnos.eventos import EventoTurno
from app.domain.turnos.turno import Turno


class CrearTurnoEntrada(BaseModel):
    """Cuerpo de la petición. No valida la zona de ``inicio``: eso es del caso de uso (D6)."""

    model_config = ConfigDict(
        extra="forbid",
        # Ejemplo para /docs: identificadores de la demo (D19).
        json_schema_extra={
            "examples": [{"paciente_id": 1, "prestacion_id": 1, "inicio": "2026-11-02T13:00:00Z"}]
        },
    )

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


class EventoTurnoSalida(BaseModel):
    """Un evento del historial del turno: los nueve campos del modelo (``04``, EventoTurno)."""

    id: int
    turno_id: int
    tipo: str
    actor_tipo: str
    actor_id: str | None
    ocurrido_en: datetime
    antes: dict[str, object] | None
    despues: dict[str, object] | None
    motivo: str | None

    @classmethod
    def desde_evento(cls, evento: EventoTurno) -> "EventoTurnoSalida":
        return cls(
            id=evento.id,
            turno_id=evento.turno_id,
            tipo=evento.tipo.value,
            actor_tipo=evento.actor_tipo.value,
            actor_id=evento.actor_id,
            ocurrido_en=evento.ocurrido_en,
            antes=evento.antes,
            despues=evento.despues,
            motivo=evento.motivo,
        )


def _nombre_normalizado(nombre: str) -> str:
    """Guarda el nombre sin espacios de más; uno vacío después de normalizar es de formato (design P9)."""
    normalizado = normalizar_espacios(nombre)
    if not normalizado:
        raise ValueError("El nombre no puede estar vacío.")
    return normalizado


NombreDePrestacion = Annotated[str, AfterValidator(_nombre_normalizado)]
ColorHexadecimal = Annotated[str, Field(pattern=r"^#[0-9A-Fa-f]{6}$")]


class CrearPrestacionEntrada(BaseModel):
    """Cuerpo de ``POST /prestaciones``. La duración la valida el dominio (RN-AG-01), no Pydantic."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"nombre": "Blanqueamiento", "duracion_minutos": 60, "color": "#3A7BD5"}]
        },
    )

    nombre: NombreDePrestacion
    duracion_minutos: int
    color: ColorHexadecimal
    reservable_online: bool = False


class EditarPrestacionEntrada(BaseModel):
    """Cuerpo de ``PATCH /prestaciones/{id}``: todo opcional; un ``null`` explícito es de formato."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"color": "#112233"}]},
    )

    nombre: NombreDePrestacion | None = None
    duracion_minutos: int | None = None
    color: ColorHexadecimal | None = None
    reservable_online: bool | None = None
    activa: bool | None = None

    @field_validator("*", mode="before")
    @classmethod
    def _sin_nulos(cls, valor: Any) -> Any:
        # Solo corre con los campos que llegan: un campo omitido no se valida ni entra en
        # ``model_fields_set``; un ``null`` explícito se rechaza nombrando el campo (V2).
        if valor is None:
            raise ValueError("El campo no admite null; omitilo para no cambiarlo.")
        return valor


class PrestacionSalida(BaseModel):
    """Una prestación del catálogo, sin ``consultorio_id`` (en la v1 hay un solo consultorio, P3)."""

    id: int
    nombre: str
    duracion_minutos: int
    color: str
    reservable_online: bool
    activa: bool

    @classmethod
    def desde_datos(cls, datos: DatosPrestacion) -> "PrestacionSalida":
        assert datos.id is not None
        return cls(
            id=datos.id,
            nombre=datos.nombre,
            duracion_minutos=datos.duracion_minutos,
            color=datos.color,
            reservable_online=datos.reservable_online,
            activa=datos.activa,
        )


class ConflictoSalida(BaseModel):
    codigo: str
    recurso: str
    recurso_id: int
    turno_id: int


class ReferenciaSalida(BaseModel):
    recurso: str
    recurso_id: int | None
    motivo: str


class ErrorDeCampoSalida(BaseModel):
    campo: str | None
    codigo: str | None
    mensaje: str


class Problema(BaseModel):
    """Cuerpo de todo error (RFC 7807, D4): seis campos comunes y las listas de su ``type``."""

    type: str
    title: str
    status: int
    detail: str
    instance: str
    codigos: list[str]
    conflictos: list[ConflictoSalida] | None = None
    referencias: list[ReferenciaSalida] | None = None
    errores: list[ErrorDeCampoSalida] | None = None
