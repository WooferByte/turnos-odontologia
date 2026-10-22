"""``/usuarios``: listar y crear los usuarios del consultorio (C-09). Endpoints síncronos (``def``, D12)."""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_hasher, get_reloj, get_uow
from app.api.esquemas import CrearUsuarioEntrada, EditarUsuarioEntrada, UsuarioSalida
from app.api.respuestas import RESPUESTAS_DE_ACCESO, _respuesta_de_error
from app.api.seguridad import requiere
from app.application.puertos import HasherDeContrasenas, UnidadDeTrabajo
from app.application.usuarios import (
    CrearUsuarioComando,
    EditarUsuarioComando,
    crear_usuario,
    editar_usuario,
    listar_usuarios,
)
from app.domain.acceso.roles import Permiso, UsuarioDelPanel
from app.domain.tiempo import Reloj

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

RESPUESTAS_DEL_ALTA = {
    **RESPUESTAS_DE_ACCESO,
    409: _respuesta_de_error("Ya existe un usuario con ese email (RN-AU-08)"),
    422: _respuesta_de_error("Entrada inválida: contraseña inicial (RN-AU-07) o formato del cuerpo"),
}

RESPUESTAS_DE_LA_EDICION = {
    **RESPUESTAS_DE_ACCESO,
    404: _respuesta_de_error("No existe el usuario (RN-GL-04)"),
    409: _respuesta_de_error("Nadie puede desactivarse a sí mismo ni dejar al consultorio sin odontólogo (RN-AU-06)"),
    422: _respuesta_de_error("Formato del cuerpo inválido"),
}


@router.get(
    "",
    response_model=list[UsuarioSalida],
    responses=RESPUESTAS_DE_ACCESO,
    dependencies=[Depends(requiere(Permiso.USUARIOS_LEER))],
)
def get_usuarios(uow: Annotated[UnidadDeTrabajo, Depends(get_uow)]) -> list[UsuarioSalida]:
    return [UsuarioSalida.desde_usuario(u) for u in listar_usuarios(uow)]


@router.post(
    "",
    status_code=201,
    response_model=UsuarioSalida,
    responses=RESPUESTAS_DEL_ALTA,
    dependencies=[Depends(requiere(Permiso.USUARIOS_EDITAR))],
)
def post_usuarios(
    entrada: CrearUsuarioEntrada,
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
    hasher: Annotated[HasherDeContrasenas, Depends(get_hasher)],
    reloj: Annotated[Reloj, Depends(get_reloj)],
) -> UsuarioSalida:
    comando = CrearUsuarioComando(
        email=entrada.email, contrasena=entrada.contrasena, roles=frozenset(entrada.roles)
    )
    return UsuarioSalida.desde_usuario(crear_usuario(comando, uow, hasher, reloj))


@router.patch("/{usuario_id}", response_model=UsuarioSalida, responses=RESPUESTAS_DE_LA_EDICION)
def patch_usuario(
    usuario_id: int,
    entrada: EditarUsuarioEntrada,
    actor: Annotated[UsuarioDelPanel, Depends(requiere(Permiso.USUARIOS_EDITAR))],
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
) -> UsuarioSalida:
    # Solo los campos que llegaron: un campo omitido no cambia (U4).
    pedidos = {campo: getattr(entrada, campo) for campo in entrada.model_fields_set}
    if pedidos.get("roles") is not None:
        pedidos["roles"] = frozenset(pedidos["roles"])
    return UsuarioSalida.desde_usuario(editar_usuario(usuario_id, EditarUsuarioComando(**pedidos), actor, uow))
