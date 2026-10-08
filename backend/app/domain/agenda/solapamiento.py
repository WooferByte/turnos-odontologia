"""Detección de solapamientos de un turno candidato (RN-AG-05, D8)."""
from collections.abc import Sequence
from dataclasses import dataclass

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
    # Grupo 5 (E2): solo se evalúa el profesional. El sillón es del grupo 6.
    # Por ahora todo turno recibido cuenta como choque: el recorte por rango lo
    # hace el repositorio y la comparación de intervalos entra en el grupo 8.
    if ocupados_profesional:
        return (
            Conflicto(
                codigo="RN-AG-05",
                recurso="profesional",
                recurso_id=profesional_id,
                turno_id=ocupados_profesional[0].turno_id,
            ),
        )
    return ()
