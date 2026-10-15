"""``/sillones``: listar, crear y editar el catálogo (C-05). Endpoints síncronos (``def``, D12)."""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_uow
from app.api.esquemas import CrearSillonEntrada, EditarSillonEntrada, SillonSalida
from app.api.respuestas import RESPUESTAS_DE_ACCESO, _respuesta_de_error
from app.api.seguridad import requiere
from app.application.puertos import UnidadDeTrabajo
from app.application.sillones import (
    CrearSillonComando,
    EditarSillonComando,
    crear_sillon,
    editar_sillon,
    listar_sillones,
)
from app.domain.acceso.roles import Permiso

router = APIRouter(prefix="/sillones", tags=["sillones"])

RESPUESTAS_DEL_ALTA = {
    **RESPUESTAS_DE_ACCESO,
    422: _respuesta_de_error("Entrada inválida: formato del cuerpo"),
}
RESPUESTAS_DE_LA_EDICION = {
    **RESPUESTAS_DE_ACCESO,
    404: _respuesta_de_error("El sillón no existe (RN-GL-04)"),
    422: _respuesta_de_error("Entrada inválida: formato de la ruta o del cuerpo"),
}


@router.get(
    "",
    response_model=list[SillonSalida],
    responses=RESPUESTAS_DE_ACCESO,
    dependencies=[Depends(requiere(Permiso.SILLONES_LEER))],
)
def get_sillones(uow: Annotated[UnidadDeTrabajo, Depends(get_uow)]) -> list[SillonSalida]:
    return [SillonSalida.desde_datos(s) for s in listar_sillones(uow)]


@router.post(
    "",
    status_code=201,
    response_model=SillonSalida,
    responses=RESPUESTAS_DEL_ALTA,
    dependencies=[Depends(requiere(Permiso.SILLONES_EDITAR))],
)
def post_sillones(
    entrada: CrearSillonEntrada, uow: Annotated[UnidadDeTrabajo, Depends(get_uow)]
) -> SillonSalida:
    return SillonSalida.desde_datos(crear_sillon(CrearSillonComando(nombre=entrada.nombre), uow))


@router.patch(
    "/{sillon_id}",
    response_model=SillonSalida,
    responses=RESPUESTAS_DE_LA_EDICION,
    dependencies=[Depends(requiere(Permiso.SILLONES_EDITAR))],
)
def patch_sillon(
    sillon_id: int,
    entrada: EditarSillonEntrada,
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
) -> SillonSalida:
    # Solo los campos que llegaron: un campo omitido no cambia.
    pedidos = {campo: getattr(entrada, campo) for campo in entrada.model_fields_set}
    editado = editar_sillon(sillon_id, EditarSillonComando(**pedidos), uow)
    return SillonSalida.desde_datos(editado)
