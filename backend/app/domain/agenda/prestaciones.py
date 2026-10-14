"""Reglas puras de las prestaciones: duración (RN-AG-01) y nombre único (RN-AG-15).

Solo biblioteca estándar (regla dura 3, design P4).
"""
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

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


def normalizar_espacios(nombre: str) -> str:
    """Quita los espacios de los extremos y colapsa los internos; es lo que se guarda."""
    return " ".join(nombre.split())


def clave_de_nombre(nombre: str) -> str:
    """Clave para comparar nombres sin mayúsculas, acentos ni espacios de más; nunca se guarda."""
    descompuesto = unicodedata.normalize("NFKD", normalizar_espacios(nombre).casefold())
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def nombre_repetido(
    nombre: str, existentes: Iterable[DatosPrestacion], excepto_id: int | None = None
) -> DatosPrestacion | None:
    """La primera prestación con la misma clave de nombre, salvo la que se está editando."""
    clave = clave_de_nombre(nombre)
    for existente in existentes:
        if existente.id != excepto_id and clave_de_nombre(existente.nombre) == clave:
            return existente
    return None
