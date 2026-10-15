"""El turno como tipo de dominio (D12). Sin id hasta que el repositorio lo guarda."""
from dataclasses import dataclass
from datetime import datetime

from app.domain.turnos.estados import EstadoTurno


@dataclass(frozen=True)
class Turno:
    consultorio_id: int
    paciente_id: int
    profesional_id: int
    sillon_id: int
    prestacion_id: int
    inicio: datetime
    fin: datetime
    duracion_minutos: int
    estado: EstadoTurno
    creado_en: datetime
    id: int | None = None
    creado_por: int | None = None  # id del usuario del panel; None en los turnos anteriores a C-07
