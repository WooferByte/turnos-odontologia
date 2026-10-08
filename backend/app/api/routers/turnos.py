"""``POST /turnos`` (D4). El endpoint es síncrono (``def``), como pide D12."""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_reloj, get_uow
from app.api.esquemas import CrearTurnoEntrada, Problema, TurnoSalida
from app.application.crear_turno import CrearTurnoComando, crear_turno
from app.application.puertos import UnidadDeTrabajo
from app.domain.tiempo import Reloj

router = APIRouter(prefix="/turnos", tags=["turnos"])

# Los errores salen como application/problem+json (RFC 7807). "model" registra el esquema
# Problema; FastAPI lo publica además bajo application/json, que acá no se usa.
_PROBLEMA_JSON = {
    "application/problem+json": {"schema": {"$ref": "#/components/schemas/Problema"}}
}
RESPUESTAS_DE_ERROR = {
    409: {
        "description": "Solapamiento con un turno activo",
        "model": Problema,
        "content": _PROBLEMA_JSON,
    },
    422: {
        "description": "Entrada inválida o intervalo inválido",
        "model": Problema,
        "content": _PROBLEMA_JSON,
    },
}


@router.post("", status_code=201, response_model=TurnoSalida, responses=RESPUESTAS_DE_ERROR)
def post_turnos(
    entrada: CrearTurnoEntrada,
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
    reloj: Annotated[Reloj, Depends(get_reloj)],
) -> TurnoSalida:
    comando = CrearTurnoComando(**entrada.model_dump())
    return TurnoSalida.desde_turno(crear_turno(comando, uow, reloj))
