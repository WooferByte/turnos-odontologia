"""Bloqueos puntuales: alcance, fechas válidas (RN-AG-17), turnos afectados (US-003 CA-2) y RN-AG-04b.

Solo biblioteca estándar (regla dura 3). Un bloqueo es el intervalo semiabierto ``[inicio, fin)``
(RN-AG-09) y su alcance sale de qué id tiene: profesional, sillón o, sin ninguno, todo el consultorio.
"""
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.agenda.intervalo import Intervalo
from app.domain.errors import BloqueoInvertido, SobreBloqueo
from app.domain.turnos.estados import ESTADOS_ACTIVOS
from app.domain.turnos.turno import Turno


class Alcance(StrEnum):
    PROFESIONAL = "profesional"
    SILLON = "sillon"
    CONSULTORIO = "consultorio"


@dataclass(frozen=True)
class DatosBloqueo:
    """El bloqueo completo. Con los dos ids a la vez no hay alcance válido: lo impide la entrada y la base (D272)."""

    id: int | None
    consultorio_id: int
    profesional_id: int | None
    sillon_id: int | None
    inicio: datetime
    fin: datetime
    motivo: str
    creado_por: int

    @property
    def alcance(self) -> Alcance:
        if self.profesional_id is not None:
            return Alcance.PROFESIONAL
        if self.sillon_id is not None:
            return Alcance.SILLON
        return Alcance.CONSULTORIO


def validar_fechas_del_bloqueo(inicio: datetime, fin: datetime) -> None:
    """``fin`` debe ser posterior a ``inicio`` (RN-AG-17, D273). Las dos fechas ya son UTC válidas."""
    if not inicio < fin:
        raise BloqueoInvertido()


def _interseca(bloqueo: DatosBloqueo, inicio: datetime, fin: datetime) -> bool:
    """La misma comparación semiabierta de ``Intervalo.se_solapa_con`` (RN-AG-09)."""
    return bloqueo.inicio < fin and inicio < bloqueo.fin


def _es_del_recurso(
    bloqueo: DatosBloqueo, profesional_id: int, sillon_id: int, consultorio_id: int
) -> bool:
    match bloqueo.alcance:
        case Alcance.PROFESIONAL:
            return bloqueo.profesional_id == profesional_id
        case Alcance.SILLON:
            return bloqueo.sillon_id == sillon_id
        case Alcance.CONSULTORIO:
            return bloqueo.consultorio_id == consultorio_id


def afecta_al_turno(bloqueo: DatosBloqueo, turno: Turno) -> bool:
    """El bloqueo es del profesional, del sillón o del consultorio del turno y los dos intervalos se intersecan."""
    return _es_del_recurso(
        bloqueo, turno.profesional_id, turno.sillon_id, turno.consultorio_id
    ) and _interseca(bloqueo, turno.inicio, turno.fin)


def turnos_afectados(bloqueo: DatosBloqueo, turnos: Sequence[Turno]) -> tuple[Turno, ...]:
    """Los turnos activos (RN-AG-10) que el bloqueo afecta, por ``(inicio, id)``. No se cancelan (D83)."""
    afectados = [t for t in turnos if t.estado in ESTADOS_ACTIVOS and afecta_al_turno(bloqueo, t)]
    return tuple(sorted(afectados, key=lambda t: (t.inicio, t.id)))


def exigir_sin_bloqueos(
    intervalo: Intervalo,
    profesional_id: int,
    sillon_id: int,
    consultorio_id: int,
    bloqueos: Sequence[DatosBloqueo],
) -> None:
    """RN-AG-04b: el turno no puede intersecar un bloqueo de su profesional, su sillón o su consultorio.

    Informa el bloqueo que empieza primero y, con el mismo inicio, el de menor id (D280, como D129).
    """
    que_afectan = [
        b
        for b in bloqueos
        if _es_del_recurso(b, profesional_id, sillon_id, consultorio_id)
        and _interseca(b, intervalo.inicio, intervalo.fin)
    ]
    if que_afectan:
        primero = min(que_afectan, key=lambda b: (b.inicio, b.id))
        raise SobreBloqueo(primero.id)
