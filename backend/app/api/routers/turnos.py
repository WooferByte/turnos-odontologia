"""``POST /turnos`` (D4) y ``GET /turnos/{id}/historial`` (H9). Endpoints síncronos (``def``, D12)."""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_reloj, get_uow
from app.api.esquemas import CrearTurnoEntrada, EventoTurnoSalida, TurnoSalida
from app.api.respuestas import RESPUESTAS_DE_ACCESO, _respuesta_de_error
from app.api.seguridad import requiere
from app.application.crear_turno import CrearTurnoComando, crear_turno
from app.application.historial import consultar_historial
from app.application.puertos import UnidadDeTrabajo
from app.domain.acceso.roles import Permiso
from app.domain.tiempo import Reloj

router = APIRouter(prefix="/turnos", tags=["turnos"])

RESPUESTAS_DE_ERROR = {
    **RESPUESTAS_DE_ACCESO,
    409: _respuesta_de_error("Solapamiento con un turno activo"),
    422: _respuesta_de_error("Entrada inválida o intervalo inválido"),
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
    dependencies=[Depends(requiere(Permiso.TURNOS_CREAR))],
)
def post_turnos(
    entrada: CrearTurnoEntrada,
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
    reloj: Annotated[Reloj, Depends(get_reloj)],
) -> TurnoSalida:
    comando = CrearTurnoComando(**entrada.model_dump())
    return TurnoSalida.desde_turno(crear_turno(comando, uow, reloj))


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
