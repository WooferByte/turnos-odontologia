"""``/bloqueos``: listar, crear y eliminar bloqueos puntuales (C-13). Endpoints síncronos (``def``, D12)."""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_uow
from app.api.esquemas import BloqueoCreadoSalida, BloqueosSalida, CrearBloqueoEntrada
from app.api.respuestas import RESPUESTAS_DE_ACCESO, _respuesta_de_error
from app.api.seguridad import requiere
from app.application.bloqueos import CrearBloqueoComando, crear_bloqueo, eliminar_bloqueo, listar_bloqueos
from app.application.puertos import UnidadDeTrabajo
from app.domain.acceso.roles import Permiso, UsuarioDelPanel

router = APIRouter(prefix="/bloqueos", tags=["bloqueos"])

RESPUESTAS_DEL_ALTA = {
    **RESPUESTAS_DE_ACCESO,
    422: _respuesta_de_error(
        "Entrada inválida: formato del cuerpo, fecha sin UTC (RN-GL-01), referencia (RN-GL-04) o fin no posterior a inicio (RN-AG-17)"
    ),
}
RESPUESTAS_DE_LA_BAJA = {
    **RESPUESTAS_DE_ACCESO,
    404: _respuesta_de_error("El bloqueo no existe (RN-GL-04)"),
    422: _respuesta_de_error("Entrada inválida: formato de la ruta"),
}


@router.get("", response_model=BloqueosSalida, responses=RESPUESTAS_DE_ACCESO)
def get_bloqueos(
    usuario: Annotated[UsuarioDelPanel, Depends(requiere(Permiso.BLOQUEOS_LEER))],
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
) -> BloqueosSalida:
    return BloqueosSalida.desde_bloqueos(listar_bloqueos(usuario.id, uow))


@router.post("", status_code=201, response_model=BloqueoCreadoSalida, responses=RESPUESTAS_DEL_ALTA)
def post_bloqueos(
    entrada: CrearBloqueoEntrada,
    usuario: Annotated[UsuarioDelPanel, Depends(requiere(Permiso.BLOQUEOS_EDITAR))],
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
) -> BloqueoCreadoSalida:
    comando = CrearBloqueoComando(
        inicio=entrada.inicio,
        fin=entrada.fin,
        motivo=entrada.motivo,
        profesional_id=entrada.profesional_id,
        sillon_id=entrada.sillon_id,
    )
    return BloqueoCreadoSalida.desde_creado(crear_bloqueo(comando, usuario.id, uow))


@router.delete("/{bloqueo_id}", status_code=204, responses=RESPUESTAS_DE_LA_BAJA)
def delete_bloqueo(
    bloqueo_id: int,
    usuario: Annotated[UsuarioDelPanel, Depends(requiere(Permiso.BLOQUEOS_EDITAR))],
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
) -> None:
    eliminar_bloqueo(bloqueo_id, usuario.id, uow)
