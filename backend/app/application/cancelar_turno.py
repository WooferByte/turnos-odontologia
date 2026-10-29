"""Caso de uso: cancelar un turno (C-17; US-013, RN-AG-12). No hace ``commit()`` ni arma SQL."""
from dataclasses import dataclass

from app.application.puertos import UnidadDeTrabajo
from app.domain.errors import TurnoNoEncontrado
from app.domain.tiempo import Reloj, utc_now
from app.domain.turnos.cancelacion import exigir_cancelable
from app.domain.turnos.estados import EstadoTurno
from app.domain.turnos.eventos import Actor, evento_cancelado
from app.domain.turnos.turno import Turno


@dataclass(frozen=True)
class CancelarTurnoComando:
    """``estado`` es quién lo pidió: ``cancelado_paciente`` o ``cancelado_profesional`` (ya validado por la API)."""

    turno_id: int
    estado: EstadoTurno


def cancelar_turno(
    comando: CancelarTurnoComando,
    usuario_id: int,
    uow: UnidadDeTrabajo,
    reloj: Reloj = utc_now,
    *,
    actor: Actor,
) -> Turno:
    """Pasa un turno activo a ``cancelado_*`` y registra el evento, todo en la misma transacción (X5, X7)."""
    with uow:
        consultorio_id = uow.usuarios.obtener(usuario_id).consultorio_id  # D270
        turno = uow.agenda.turno_para_cambiar(comando.turno_id)
        if turno is None or turno.consultorio_id != consultorio_id:
            raise TurnoNoEncontrado(comando.turno_id)
        exigir_cancelable(turno.estado)
        guardado = uow.agenda.cambiar_estado(turno.id, comando.estado)
        uow.historial.registrar(evento_cancelado(turno, guardado, actor, reloj()))
        return guardado
