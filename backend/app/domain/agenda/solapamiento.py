"""Detección de solapamientos de un turno candidato (RN-AG-05, D8)."""
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from app.domain.agenda.intervalo import Intervalo
from app.domain.errors import Conflicto
from app.domain.turnos.estados import EstadoTurno


@dataclass(frozen=True)
class TurnoOcupado:
    turno_id: int
    intervalo: Intervalo
    estado: EstadoTurno


def detectar_conflictos(
    candidato: Intervalo,
    profesional_id: int,
    ocupados_profesional: Sequence[TurnoOcupado],
    sillon_id: int,
    ocupados_sillon: Sequence[TurnoOcupado],
) -> tuple[Conflicto, ...]:
    # Por ahora todo turno recibido cuenta como choque: el recorte por rango lo
    # hace el repositorio y la comparación de intervalos entra en el grupo 8.
    # Primero el profesional, después el sillón.
    posibles = (
        _conflicto_de_recurso("RN-AG-05", "profesional", profesional_id, ocupados_profesional),
        _conflicto_de_recurso("RN-AG-08", "sillon", sillon_id, ocupados_sillon),
    )
    return tuple(c for c in posibles if c is not None)


def _conflicto_de_recurso(
    codigo: Literal["RN-AG-05", "RN-AG-08"],
    recurso: Literal["profesional", "sillon"],
    recurso_id: int,
    ocupados: Sequence[TurnoOcupado],
) -> Conflicto | None:
    if not ocupados:
        return None
    primero = min(ocupados, key=lambda ocupado: ocupado.intervalo.inicio)  # D129
    return Conflicto(codigo=codigo, recurso=recurso, recurso_id=recurso_id, turno_id=primero.turno_id)
