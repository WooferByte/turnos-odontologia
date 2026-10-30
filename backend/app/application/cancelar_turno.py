"""Caso de uso: cancelar un turno (C-17; US-013, RN-AG-12). No hace ``commit()`` ni arma SQL."""
from dataclasses import dataclass

from app.application.puertos import UnidadDeTrabajo
from app.application.turno_propio import turno_propio_para_cambiar
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
        turno = turno_propio_para_cambiar(uow, usuario_id, comando.turno_id)
        exigir_cancelable(turno.estado)
        guardado = uow.agenda.cambiar_estado(turno.id, comando.estado)
        uow.historial.registrar(evento_cancelado(turno, guardado, actor, reloj()))
        return guardado
