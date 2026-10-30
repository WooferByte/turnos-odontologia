"""Datos mínimos de los recursos de la agenda que necesita el dominio (D12)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Prestacion:
    id: int
    consultorio_id: int
    duracion_minutos: int
    activa: bool


@dataclass(frozen=True)
class Profesional:
    id: int
    consultorio_id: int
    activo: bool


@dataclass(frozen=True)
class Paciente:
    id: int
    consultorio_id: int
    es_nuevo: bool = True  # RN-TD-05: nuevo hasta su primer turno atendido


@dataclass(frozen=True)
class Sillon:
    id: int
    consultorio_id: int
    activo: bool
