"""Estados del turno (04_modelo_de_datos.md)."""
from enum import StrEnum


class EstadoTurno(StrEnum):
    PENDIENTE_APROBACION = "pendiente_aprobacion"
    PENDIENTE_SENA = "pendiente_sena"
    RESERVADO = "reservado"
    CONFIRMADO = "confirmado"
    CANCELADO_PACIENTE = "cancelado_paciente"
    CANCELADO_PROFESIONAL = "cancelado_profesional"
    VENCIDO = "vencido"
    ATENDIDO = "atendido"
    AUSENTE = "ausente"


# Solo estos estados ocupan el horario (RN-AG-10); el resto lo libera.
ESTADOS_ACTIVOS = frozenset(
    {
        EstadoTurno.PENDIENTE_APROBACION,
        EstadoTurno.PENDIENTE_SENA,
        EstadoTurno.RESERVADO,
        EstadoTurno.CONFIRMADO,
    }
)
