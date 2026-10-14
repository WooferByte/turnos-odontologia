"""El sillón del catálogo (US-004). Solo biblioteca estándar (regla dura 3, design S4)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DatosSillon:
    """El sillón completo; ``recursos.Sillon`` es solo lo que usa crear_turno."""

    id: int | None
    consultorio_id: int
    nombre: str
    activo: bool
