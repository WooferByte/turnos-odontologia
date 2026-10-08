"""Errores de dominio. Cada uno lleva el código de su regla (RN-XX)."""
from dataclasses import dataclass
from typing import Literal


class ErrorDeDominio(Exception):
    codigo: str
    mensaje: str

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje

    @property
    def codigos(self) -> list[str]:
        return [self.codigo]


# --- Validación de entrada (se informa toda junta) ---
class FechaNoUTC(ErrorDeDominio):
    codigo = "RN-GL-01"

    def __init__(self, campo: str) -> None:
        self.campo = campo
        super().__init__(
            f"El campo '{campo}' debe ser una fecha y hora con zona y en UTC, "
            "por ejemplo 2026-11-02T13:00:00Z."
        )


# --- Reglas de negocio (de a una) ---
class IntervaloInvalido(ErrorDeDominio):
    codigo = "RN-AG-10d"


@dataclass(frozen=True)
class Conflicto:
    codigo: Literal["RN-AG-05", "RN-AG-08"]
    recurso: Literal["profesional", "sillon"]
    recurso_id: int
    turno_id: int


class ErrorDeSolapamiento(ErrorDeDominio):
    """Una sola regla de negocio que mira dos recursos: lleva uno o dos conflictos (D6)."""

    conflictos: tuple[Conflicto, ...]

    def __init__(self, conflictos: tuple[Conflicto, ...]) -> None:
        self.conflictos = conflictos
        self.codigo = conflictos[0].codigo
        detalle = "; ".join(
            f"el {c.recurso} {c.recurso_id} ya tiene el turno {c.turno_id} activo en ese horario"
            for c in conflictos
        )
        super().__init__(f"El turno se solapa con otro: {detalle}.")

    @property
    def codigos(self) -> list[str]:
        return [c.codigo for c in self.conflictos]
