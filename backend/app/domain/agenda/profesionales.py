"""El profesional tal como lo muestra la API de horario (US-002). Solo biblioteca estándar (regla dura 3)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DatosProfesional:
    """El profesional completo; ``recursos.Profesional`` es solo lo que usa crear_turno."""

    id: int
    consultorio_id: int
    nombre: str
    activo: bool
