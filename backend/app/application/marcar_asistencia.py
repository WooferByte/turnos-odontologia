"""Caso de uso: marcar un turno atendido o ausente (C-18; US-014, RN-AG-12, RN-AG-13). No hace ``commit()`` ni arma SQL."""
from dataclasses import dataclass

from app.application.puertos import UnidadDeTrabajo
from app.application.turno_propio import turno_propio_para_cambiar
from app.domain.tiempo import Reloj, utc_now
from app.domain.turnos.asistencia import deja_de_ser_nuevo, exigir_marcable
from app.domain.turnos.estados import EstadoTurno
from app.domain.turnos.eventos import Actor, evento_estado_cambiado
from app.domain.turnos.turno import Turno


@dataclass(frozen=True)
class MarcarAsistenciaComando:
    """``estado`` es ``atendido`` o ``ausente`` (ya validado por la API)."""

    turno_id: int
    estado: EstadoTurno


def marcar_asistencia(
    comando: MarcarAsistenciaComando,
    usuario_id: int,
    uow: UnidadDeTrabajo,
    reloj: Reloj = utc_now,
    *,
    actor: Actor,
) -> Turno:
    """Pasa un turno ``reservado`` o ``confirmado`` a ``atendido`` o ``ausente`` y registra el evento (W6).

    Todo en la misma transacción. No relee profesional, sillón ni prestación: un turno cuyos recursos se
    desactivaron después de crearlo se marca igual (ASI-1f).
    """
    with uow:
        turno = turno_propio_para_cambiar(uow, usuario_id, comando.turno_id)
        ahora = reloj()  # un solo instante: decide RN-AG-13 y queda en ``ocurrido_en``
        exigir_marcable(turno.estado, turno.inicio, ahora)
        guardado = uow.agenda.cambiar_estado(turno.id, comando.estado)
        if deja_de_ser_nuevo(comando.estado):
            uow.agenda.marcar_paciente_no_nuevo(turno.paciente_id)
        uow.historial.registrar(evento_estado_cambiado(turno, guardado, actor, ahora))
        return guardado
