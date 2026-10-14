"""``/prestaciones``: listar, crear y editar el catálogo (C-04). Endpoints síncronos (``def``, D12)."""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_uow
from app.api.esquemas import (
    CrearPrestacionEntrada,
    EditarPrestacionEntrada,
    PrestacionSalida,
)
from app.api.respuestas import _respuesta_de_error
from app.application.prestaciones import (
    CrearPrestacionComando,
    EditarPrestacionComando,
    crear_prestacion,
    editar_prestacion,
    listar_prestaciones,
)
from app.application.puertos import UnidadDeTrabajo

router = APIRouter(prefix="/prestaciones", tags=["prestaciones"])

RESPUESTAS_DEL_ALTA = {
    409: _respuesta_de_error("Ya existe una prestación con ese nombre (RN-AG-15)"),
    422: _respuesta_de_error("Entrada inválida: duración (RN-AG-01) o formato del cuerpo"),
}
RESPUESTAS_DE_LA_EDICION = {
    404: _respuesta_de_error("La prestación no existe (RN-GL-04)"),
    409: _respuesta_de_error("Ya existe otra prestación con ese nombre (RN-AG-15)"),
    422: _respuesta_de_error("Entrada inválida: duración (RN-AG-01) o formato de la ruta o del cuerpo"),
}


@router.get("", response_model=list[PrestacionSalida])
def get_prestaciones(uow: Annotated[UnidadDeTrabajo, Depends(get_uow)]) -> list[PrestacionSalida]:
    return [PrestacionSalida.desde_datos(p) for p in listar_prestaciones(uow)]


@router.post("", status_code=201, response_model=PrestacionSalida, responses=RESPUESTAS_DEL_ALTA)
def post_prestaciones(
    entrada: CrearPrestacionEntrada, uow: Annotated[UnidadDeTrabajo, Depends(get_uow)]
) -> PrestacionSalida:
    comando = CrearPrestacionComando(**entrada.model_dump())
    return PrestacionSalida.desde_datos(crear_prestacion(comando, uow))


@router.patch(
    "/{prestacion_id}", response_model=PrestacionSalida, responses=RESPUESTAS_DE_LA_EDICION
)
def patch_prestacion(
    prestacion_id: int,
    entrada: EditarPrestacionEntrada,
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
) -> PrestacionSalida:
    # Solo los campos que llegaron: un campo omitido no cambia (design P9).
    pedidos = {campo: getattr(entrada, campo) for campo in entrada.model_fields_set}
    editada = editar_prestacion(prestacion_id, EditarPrestacionComando(**pedidos), uow)
    return PrestacionSalida.desde_datos(editada)
