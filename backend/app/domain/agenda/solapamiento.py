"""Detección de solapamientos de un turno candidato (RN-AG-05, D8)."""
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from app.domain.agenda.intervalo import Intervalo
from app.domain.errors import Conflicto
from app.domain.turnos.estados import ESTADOS_ACTIVOS, EstadoTurno


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
    # El repositorio puede devolver turnos de otro horario del recurso: la regla de
    # solapamiento (RN-AG-09) la decide el dominio con Intervalo.se_solapa_con.
    # Primero el profesional, después el sillón.
    posibles = (
        _conflicto_de_recurso(
            "RN-AG-05", "profesional", profesional_id, candidato, ocupados_profesional
        ),
        _conflicto_de_recurso("RN-AG-08", "sillon", sillon_id, candidato, ocupados_sillon),
    )
    return tuple(c for c in posibles if c is not None)


def _conflicto_de_recurso(
    codigo: Literal["RN-AG-05", "RN-AG-08"],
    recurso: Literal["profesional", "sillon"],
    recurso_id: int,
    candidato: Intervalo,
    ocupados: Sequence[TurnoOcupado],
) -> Conflicto | None:
    que_chocan = [
        o
        for o in ocupados
        if o.estado in ESTADOS_ACTIVOS and o.intervalo.se_solapa_con(candidato)  # RN-AG-10
    ]
    if not que_chocan:
        return None
    primero = min(que_chocan, key=lambda ocupado: ocupado.intervalo.inicio)  # D129
    return Conflicto(codigo=codigo, recurso=recurso, recurso_id=recurso_id, turno_id=primero.turno_id)
