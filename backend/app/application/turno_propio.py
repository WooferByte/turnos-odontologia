"""Lectura con bloqueo del turno que un caso de uso va a cambiar (cancelar, reprogramar, marcar; D166, D270, D321)."""
from app.application.puertos import UnidadDeTrabajo
from app.domain.errors import TurnoNoEncontrado
from app.domain.turnos.turno import Turno


def turno_propio_para_cambiar(uow: UnidadDeTrabajo, usuario_id: int, turno_id: int) -> Turno:
    """El turno con bloqueo de fila; ``TurnoNoEncontrado`` si no existe o es de otro consultorio. Dentro de un ``with uow:``."""
    consultorio_id = uow.usuarios.obtener(usuario_id).consultorio_id  # D270
    turno = uow.agenda.turno_para_cambiar(turno_id)
    if turno is None or turno.consultorio_id != consultorio_id:
        raise TurnoNoEncontrado(turno_id)
    return turno
