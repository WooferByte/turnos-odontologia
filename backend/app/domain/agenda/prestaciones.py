"""Reglas puras de las prestaciones: duración (RN-AG-01) y nombre único (RN-AG-15).

Solo biblioteca estándar (regla dura 3, design P4).
"""
from collections.abc import Iterable
from dataclasses import dataclass

from app.domain.agenda.nombres import clave_de_nombre

GRANULARIDAD_MINUTOS = 5  # D99; C-22 la reemplaza por ConfiguracionReglas


@dataclass(frozen=True)
class DatosPrestacion:
    """La prestación del catálogo completa; ``recursos.Prestacion`` es solo lo que usa crear_turno."""

    id: int | None
    consultorio_id: int
    nombre: str
    duracion_minutos: int
    color: str
    reservable_online: bool
    activa: bool


def duracion_valida(minutos: int, granularidad: int = GRANULARIDAD_MINUTOS) -> bool:
    return minutos > 0 and minutos % granularidad == 0


def nombre_repetido(
    nombre: str, existentes: Iterable[DatosPrestacion], excepto_id: int | None = None
) -> DatosPrestacion | None:
    """La primera prestación con la misma clave de nombre, salvo la que se está editando."""
    clave = clave_de_nombre(nombre)
    for existente in existentes:
        if existente.id != excepto_id and clave_de_nombre(existente.nombre) == clave:
            return existente
    return None
