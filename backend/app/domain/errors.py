"""Errores de dominio. Cada uno lleva el código de su regla (RN-XX)."""


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
