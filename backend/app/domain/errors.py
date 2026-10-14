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


class DuracionInvalida(ErrorDeDominio):
    """La duración no es mayor que 0 o no es múltiplo de la granularidad (RN-AG-01)."""

    codigo = "RN-AG-01"

    def __init__(self, granularidad: int, campo: str = "duracion_minutos") -> None:
        self.campo = campo
        self.granularidad = granularidad
        super().__init__(
            f"El campo '{campo}' debe ser mayor que 0 y múltiplo de {granularidad} minutos."
        )


@dataclass(frozen=True)
class ReferenciaInvalida:
    recurso: Literal["prestacion", "paciente", "profesional", "sillon", "turno"]
    recurso_id: int | None
    motivo: Literal["inexistente", "inactivo", "ninguno_activo", "varios_activos"]


class RecursoNoEncontrado(ErrorDeDominio):
    """Una o más referencias inválidas bajo un único código RN-GL-04 (D7)."""

    codigo = "RN-GL-04"
    referencias: tuple[ReferenciaInvalida, ...]

    def __init__(self, referencias: tuple[ReferenciaInvalida, ...]) -> None:
        self.referencias = referencias
        detalle = "; ".join(f"{r.recurso} {r.recurso_id} ({r.motivo})" for r in referencias)
        super().__init__(f"Referencias inválidas: {detalle}.")


class RecursoDeLaUrlNoEncontrado(ErrorDeDominio):
    """El recurso que nombra la URL no existe (RN-GL-04): sale como 404, no como 422."""

    codigo = "RN-GL-04"
    referencias: tuple[ReferenciaInvalida, ...]

    def __init__(
        self,
        recurso: Literal["prestacion", "sillon", "turno"],
        recurso_id: int,
        mensaje: str,
    ) -> None:
        self.referencias = (ReferenciaInvalida(recurso, recurso_id, "inexistente"),)
        super().__init__(mensaje)


class TurnoNoEncontrado(RecursoDeLaUrlNoEncontrado):
    def __init__(self, turno_id: int) -> None:
        super().__init__("turno", turno_id, f"No existe el turno {turno_id}.")


class PrestacionNoEncontrada(RecursoDeLaUrlNoEncontrado):
    def __init__(self, prestacion_id: int) -> None:
        super().__init__("prestacion", prestacion_id, f"No existe la prestación {prestacion_id}.")


class SillonNoEncontrado(RecursoDeLaUrlNoEncontrado):
    def __init__(self, sillon_id: int) -> None:
        super().__init__("sillon", sillon_id, f"No existe el sillón {sillon_id}.")


class EntradaInvalida(ErrorDeDominio):
    """Toda la validación de entrada junta: ``FechaNoUTC``, ``DuracionInvalida`` y/o ``RecursoNoEncontrado`` (D6)."""

    errores: tuple[ErrorDeDominio, ...]

    def __init__(self, errores: tuple[ErrorDeDominio, ...]) -> None:
        self.errores = errores
        self.codigo = errores[0].codigo
        detalle = " ".join(e.mensaje for e in errores)
        super().__init__(f"La petición tiene problemas de entrada. {detalle}")

    @property
    def codigos(self) -> list[str]:
        return [e.codigo for e in self.errores]

    @property
    def referencias(self) -> tuple[ReferenciaInvalida, ...]:
        for error in self.errores:
            if isinstance(error, RecursoNoEncontrado):
                return error.referencias
        return ()


# --- Reglas de negocio (de a una) ---
class NombreDePrestacionRepetido(ErrorDeDominio):
    """El nombre ya lo usa otra prestación del consultorio, activa o inactiva (RN-AG-15)."""

    codigo = "RN-AG-15"

    def __init__(self, nombre_existente: str) -> None:
        self.nombre_existente = nombre_existente
        super().__init__(f"Ya existe una prestación llamada «{nombre_existente}».")


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


# --- Acceso (US-090, US-094): el mensaje es fijo y no nombra al usuario ni la causa (D200) ---
class CredencialesInvalidas(ErrorDeDominio):
    """Email o contraseña incorrectos, o usuario inactivo: no se distinguen (RN-AU-04)."""

    codigo = "RN-AU-04"

    def __init__(self) -> None:
        super().__init__("El email o la contraseña no son correctos.")


class SesionInvalida(ErrorDeDominio):
    """El token no sirve: ilegible, vencido, de otro tipo o de un usuario que ya no puede (RN-AU-03)."""

    codigo = "RN-AU-03"

    def __init__(self) -> None:
        super().__init__("La sesión no es válida o venció. Iniciá sesión de nuevo.")
