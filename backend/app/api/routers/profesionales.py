"""``/profesionales``: lista y horario recurrente (C-12). Endpoints síncronos (``def``, D12)."""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_uow
from app.api.esquemas import HorarioSalida, ProfesionalSalida, ReemplazarHorarioEntrada
from app.api.respuestas import RESPUESTAS_DE_ACCESO, _respuesta_de_error
from app.api.seguridad import requiere
from app.application.horario import listar_profesionales, obtener_horario, reemplazar_horario
from app.application.puertos import UnidadDeTrabajo
from app.domain.acceso.roles import Permiso, UsuarioDelPanel

router = APIRouter(prefix="/profesionales", tags=["profesionales"])

RESPUESTAS_DE_LA_LECTURA = {
    **RESPUESTAS_DE_ACCESO,
    404: _respuesta_de_error("El profesional no existe (RN-GL-04)"),
    422: _respuesta_de_error("Entrada inválida: formato de la ruta"),
}
RESPUESTAS_DEL_REEMPLAZO = {
    **RESPUESTAS_DE_ACCESO,
    404: _respuesta_de_error("El profesional no existe (RN-GL-04)"),
    422: _respuesta_de_error("Entrada inválida: formato ruta o cuerpo, o franjas superpuestas (RN-AG-16)"),
}


@router.get("", response_model=list[ProfesionalSalida], responses=RESPUESTAS_DE_ACCESO)
def get_profesionales(
    usuario: Annotated[UsuarioDelPanel, Depends(requiere(Permiso.PROFESIONALES_LEER))],
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
) -> list[ProfesionalSalida]:
    return [ProfesionalSalida.desde_datos(p) for p in listar_profesionales(usuario.id, uow)]


@router.get(
    "/{profesional_id}/horario", response_model=HorarioSalida, responses=RESPUESTAS_DE_LA_LECTURA
)
def get_horario(
    profesional_id: int,
    usuario: Annotated[UsuarioDelPanel, Depends(requiere(Permiso.HORARIO_LEER))],
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
) -> HorarioSalida:
    return HorarioSalida.desde_horario(obtener_horario(profesional_id, usuario.id, uow))


@router.put(
    "/{profesional_id}/horario", response_model=HorarioSalida, responses=RESPUESTAS_DEL_REEMPLAZO
)
def put_horario(
    profesional_id: int,
    entrada: ReemplazarHorarioEntrada,
    usuario: Annotated[UsuarioDelPanel, Depends(requiere(Permiso.HORARIO_EDITAR))],
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
) -> HorarioSalida:
    franjas = [f.a_dominio() for f in entrada.franjas]
    return HorarioSalida.desde_horario(reemplazar_horario(profesional_id, franjas, usuario.id, uow))
