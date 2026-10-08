"""``POST /turnos`` (D4). El endpoint es síncrono (``def``), como pide D12."""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_reloj, get_uow
from app.api.esquemas import CrearTurnoEntrada, TurnoSalida
from app.application.crear_turno import CrearTurnoComando, crear_turno
from app.application.puertos import UnidadDeTrabajo
from app.domain.tiempo import Reloj

router = APIRouter(prefix="/turnos", tags=["turnos"])


@router.post("", status_code=201, response_model=TurnoSalida)
def post_turnos(
    entrada: CrearTurnoEntrada,
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
    reloj: Annotated[Reloj, Depends(get_reloj)],
) -> TurnoSalida:
    comando = CrearTurnoComando(**entrada.model_dump())
    return TurnoSalida.desde_turno(crear_turno(comando, uow, reloj))
