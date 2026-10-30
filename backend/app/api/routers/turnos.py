"""``POST /turnos`` (D4), ``GET /turnos`` y ``GET /turnos/{id}`` (C-14) y ``GET /turnos/{id}/historial`` (H9). Endpoints síncronos (``def``, D12)."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_reloj, get_uow
from app.api.esquemas import (
    CancelarTurnoEntrada,
    AgendaDelDiaSalida,
    CrearTurnoEntrada,
    EventoTurnoSalida,
    FechaDelDia,
    MarcarAsistenciaEntrada,
    ReprogramarTurnoEntrada,
    TurnoDeLaAgendaSalida,
    TurnoSalida,
)
from app.api.respuestas import RESPUESTAS_DE_ACCESO, _respuesta_de_error
from app.api.seguridad import requiere
from app.application.cancelar_turno import CancelarTurnoComando, cancelar_turno
from app.application.crear_turno import CrearTurnoComando, crear_turno
from app.application.consultar_turnos import agenda_del_dia, turno_de_la_agenda
from app.application.historial import consultar_historial
from app.application.marcar_asistencia import MarcarAsistenciaComando, marcar_asistencia
from app.application.puertos import UnidadDeTrabajo
from app.application.reprogramar_turno import ReprogramarTurnoComando, reprogramar_turno
from app.domain.acceso.roles import Permiso, UsuarioDelPanel
from app.domain.tiempo import Reloj
from app.domain.turnos.estados import EstadoTurno
from app.domain.turnos.eventos import Actor, ActorTipo

router = APIRouter(prefix="/turnos", tags=["turnos"])

RESPUESTAS_DE_ERROR = {
    **RESPUESTAS_DE_ACCESO,
    409: _respuesta_de_error("Solapamiento con un turno activo"),
    422: _respuesta_de_error("Entrada inválida o intervalo inválido"),
}
RESPUESTAS_DE_LA_AGENDA = {
    **RESPUESTAS_DE_ACCESO,
    422: _respuesta_de_error("La fecha no es un día aaaa-mm-dd entre 0001-01-02 y 9999-12-30"),
}
RESPUESTAS_DE_UN_TURNO = {
    **RESPUESTAS_DE_ACCESO,
    404: _respuesta_de_error("El turno no existe o es de otro consultorio (RN-GL-04)"),
    422: _respuesta_de_error("El identificador del turno no es un número entero"),
}
RESPUESTAS_DE_REPROGRAMAR = {
    **RESPUESTAS_DE_ACCESO,
    404: _respuesta_de_error("El turno no existe o es de otro consultorio (RN-GL-04)"),
    409: _respuesta_de_error("Solapamiento con un turno activo (RN-AG-05, RN-AG-08) o turno no reprogramable (RN-AG-18)"),
    422: _respuesta_de_error("Entrada inválida (RN-GL-01, RN-AG-01), intervalo inválido, fuera de horario o sobre un bloqueo"),
}
RESPUESTAS_DE_CANCELAR = {
    **RESPUESTAS_DE_ACCESO,
    404: _respuesta_de_error("El turno no existe o es de otro consultorio (RN-GL-04)"),
    409: _respuesta_de_error("El turno no está activo y no se puede cancelar (RN-AG-12)"),
    422: _respuesta_de_error("El estado no es cancelado_paciente ni cancelado_profesional o el identificador no es entero"),
}
RESPUESTAS_DE_MARCAR = {
    **RESPUESTAS_DE_ACCESO,
    404: _respuesta_de_error("El turno no existe o es de otro consultorio (RN-GL-04)"),
    409: _respuesta_de_error("El turno no admite el marcado en su estado (RN-AG-12) o todavía no empezó (RN-AG-13)"),
    422: _respuesta_de_error("El estado no es atendido ni ausente o el identificador no es entero"),
}
RESPUESTAS_DEL_HISTORIAL = {
    **RESPUESTAS_DE_ACCESO,
    404: _respuesta_de_error("El turno no existe (RN-GL-04)"),
    422: _respuesta_de_error("El identificador del turno no es un número entero"),
}


@router.post(
    "",
    status_code=201,
    response_model=TurnoSalida,
    responses=RESPUESTAS_DE_ERROR,
)
def post_turnos(
    entrada: CrearTurnoEntrada,
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
    reloj: Annotated[Reloj, Depends(get_reloj)],
    usuario: Annotated[UsuarioDelPanel, Depends(requiere(Permiso.TURNOS_CREAR))],
) -> TurnoSalida:
    comando = CrearTurnoComando(**entrada.model_dump())
    actor = Actor(ActorTipo.USUARIO, str(usuario.id))  # el id va como texto decimal (D209)
    return TurnoSalida.desde_turno(
        crear_turno(comando, uow, reloj, actor=actor, creado_por=usuario.id)
    )


@router.patch("/{turno_id}", response_model=TurnoSalida, responses=RESPUESTAS_DE_REPROGRAMAR)
def patch_turno(
    turno_id: int,
    entrada: ReprogramarTurnoEntrada,
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
    reloj: Annotated[Reloj, Depends(get_reloj)],
    usuario: Annotated[UsuarioDelPanel, Depends(requiere(Permiso.TURNOS_REPROGRAMAR))],
) -> TurnoSalida:
    """Mueve el turno o le cambia la duración (US-012); un campo omitido conserva su valor."""
    comando = ReprogramarTurnoComando(turno_id, entrada.inicio, entrada.duracion_minutos)
    actor = Actor(ActorTipo.USUARIO, str(usuario.id))  # el id va como texto decimal (D209)
    return TurnoSalida.desde_turno(reprogramar_turno(comando, usuario.id, uow, reloj, actor=actor))


@router.post("/{turno_id}/cancelar", response_model=TurnoSalida, responses=RESPUESTAS_DE_CANCELAR)
def post_cancelar_turno(
    turno_id: int,
    entrada: CancelarTurnoEntrada,
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
    reloj: Annotated[Reloj, Depends(get_reloj)],
    usuario: Annotated[UsuarioDelPanel, Depends(requiere(Permiso.TURNOS_CANCELAR))],
) -> TurnoSalida:
    """Cancela un turno activo indicando quién lo pidió y libera su horario (US-013)."""
    comando = CancelarTurnoComando(turno_id, EstadoTurno(entrada.estado))
    actor = Actor(ActorTipo.USUARIO, str(usuario.id))  # el id va como texto decimal (D209)
    return TurnoSalida.desde_turno(cancelar_turno(comando, usuario.id, uow, reloj, actor=actor))


@router.post("/{turno_id}/estado", response_model=TurnoSalida, responses=RESPUESTAS_DE_MARCAR)
def post_estado_del_turno(
    turno_id: int,
    entrada: MarcarAsistenciaEntrada,
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
    reloj: Annotated[Reloj, Depends(get_reloj)],
    usuario: Annotated[UsuarioDelPanel, Depends(requiere(Permiso.TURNOS_MARCAR))],
) -> TurnoSalida:
    """Marca un turno ya empezado como atendido o ausente (US-014)."""
    comando = MarcarAsistenciaComando(turno_id, EstadoTurno(entrada.estado))
    actor = Actor(ActorTipo.USUARIO, str(usuario.id))  # el id va como texto decimal (D209)
    return TurnoSalida.desde_turno(marcar_asistencia(comando, usuario.id, uow, reloj, actor=actor))


@router.get("", response_model=AgendaDelDiaSalida, responses=RESPUESTAS_DE_LA_AGENDA)
def get_turnos(
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
    reloj: Annotated[Reloj, Depends(get_reloj)],
    usuario: Annotated[UsuarioDelPanel, Depends(requiere(Permiso.TURNOS_LEER))],
    fecha: Annotated[
        FechaDelDia | None,
        Query(description="Día del consultorio (aaaa-mm-dd). Sin ella, el día de hoy del consultorio."),
    ] = None,
) -> AgendaDelDiaSalida:
    return AgendaDelDiaSalida.desde_agenda(agenda_del_dia(fecha, usuario.id, uow, reloj))


@router.get("/{turno_id}", response_model=TurnoDeLaAgendaSalida, responses=RESPUESTAS_DE_UN_TURNO)
def get_turno(
    turno_id: int,
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
    usuario: Annotated[UsuarioDelPanel, Depends(requiere(Permiso.TURNOS_LEER))],
) -> TurnoDeLaAgendaSalida:
    return TurnoDeLaAgendaSalida.desde_turno(turno_de_la_agenda(turno_id, usuario.id, uow))


@router.get(
    "/{turno_id}/historial",
    response_model=list[EventoTurnoSalida],
    responses=RESPUESTAS_DEL_HISTORIAL,
    dependencies=[Depends(requiere(Permiso.HISTORIAL_LEER))],
)
def get_historial(
    turno_id: int, uow: Annotated[UnidadDeTrabajo, Depends(get_uow)]
) -> list[EventoTurnoSalida]:
    return [EventoTurnoSalida.desde_evento(e) for e in consultar_historial(turno_id, uow)]
