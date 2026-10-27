"""``/auth``: iniciar sesión y renovarla (C-06). Endpoints síncronos (``def``, D12)."""
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_firmador, get_hasher, get_reloj, get_uow, get_vigencias
from app.api.esquemas import (
    AccessSalida,
    CambiarContrasenaEntrada,
    LoginEntrada,
    RefreshEntrada,
    TokensSalida,
    UsuarioDeLaSesionSalida,
)
from app.api.seguridad import requiere
from app.api.respuestas import RESPUESTAS_DE_ACCESO, _respuesta_de_error
from app.application.acceso import usuario_de_la_sesion
from app.application.puertos import FirmadorDeTokens, HasherDeContrasenas, UnidadDeTrabajo
from app.application.sesion import (
    IniciarSesionComando,
    Vigencias,
    cambiar_contrasena,
    iniciar_sesion,
    renovar_sesion,
)
from app.domain.acceso.roles import Permiso, UsuarioDelPanel
from app.domain.tiempo import Reloj

router = APIRouter(prefix="/auth", tags=["auth"])

RESPUESTAS_DEL_LOGIN = {
    401: _respuesta_de_error("Email o contraseña incorrectos, o usuario inactivo (RN-AU-04)"),
    422: _respuesta_de_error("Entrada inválida: formato del cuerpo"),
}
RESPUESTAS_DEL_REFRESH = {
    401: _respuesta_de_error("El refresh token no sirve (RN-AU-03)"),
    422: _respuesta_de_error("Entrada inválida: formato del cuerpo"),
}
RESPUESTAS_DEL_CAMBIO_DE_CONTRASENA = {
    **RESPUESTAS_DE_ACCESO,
    422: _respuesta_de_error(
        "Entrada inválida: contraseña nueva de 10 caracteres a 72 bytes (RN-AU-07), formato del cuerpo "
        "o contraseña actual incorrecta (RN-AU-09)"
    ),
}


def _sin_cache(respuesta: Response) -> None:
    """RFC 6749 §5.1: una respuesta con tokens no se guarda en ninguna caché."""
    respuesta.headers["Cache-Control"] = "no-store"


@router.post("/login", response_model=TokensSalida, responses=RESPUESTAS_DEL_LOGIN)
def post_login(
    entrada: LoginEntrada,
    respuesta: Response,
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
    hasher: Annotated[HasherDeContrasenas, Depends(get_hasher)],
    firmador: Annotated[FirmadorDeTokens, Depends(get_firmador)],
    vigencias: Annotated[Vigencias, Depends(get_vigencias)],
    reloj: Annotated[Reloj, Depends(get_reloj)],
) -> TokensSalida:
    tokens = iniciar_sesion(
        IniciarSesionComando(email=entrada.email, contrasena=entrada.contrasena),
        uow, hasher, firmador, vigencias, reloj,
    )
    _sin_cache(respuesta)
    return TokensSalida(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=int(vigencias.access.total_seconds()),
    )


@router.post("/refresh", response_model=AccessSalida, responses=RESPUESTAS_DEL_REFRESH)
def post_refresh(
    entrada: RefreshEntrada,
    respuesta: Response,
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
    firmador: Annotated[FirmadorDeTokens, Depends(get_firmador)],
    vigencias: Annotated[Vigencias, Depends(get_vigencias)],
    reloj: Annotated[Reloj, Depends(get_reloj)],
) -> AccessSalida:
    nuevo = renovar_sesion(entrada.refresh_token, uow, firmador, vigencias, reloj)
    _sin_cache(respuesta)
    return AccessSalida(access_token=nuevo.access_token, expires_in=int(vigencias.access.total_seconds()))


@router.post("/cambiar-contrasena", response_model=TokensSalida, responses=RESPUESTAS_DEL_CAMBIO_DE_CONTRASENA)
def post_cambiar_contrasena(
    entrada: CambiarContrasenaEntrada,
    respuesta: Response,
    actor: Annotated[UsuarioDelPanel, Depends(requiere(Permiso.CONTRASENA_PROPIA))],
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
    hasher: Annotated[HasherDeContrasenas, Depends(get_hasher)],
    firmador: Annotated[FirmadorDeTokens, Depends(get_firmador)],
    vigencias: Annotated[Vigencias, Depends(get_vigencias)],
    reloj: Annotated[Reloj, Depends(get_reloj)],
) -> TokensSalida:
    tokens = cambiar_contrasena(
        actor, entrada.contrasena_actual, entrada.contrasena_nueva, uow, hasher, firmador, vigencias, reloj
    )
    _sin_cache(respuesta)
    return TokensSalida(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=int(vigencias.access.total_seconds()),
    )


@router.get("/yo", response_model=UsuarioDeLaSesionSalida, responses=RESPUESTAS_DE_ACCESO)
def get_yo(
    respuesta: Response,
    actor: Annotated[UsuarioDelPanel, Depends(requiere(Permiso.SESION_LEER))],
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
) -> UsuarioDeLaSesionSalida:
    """Email y roles de quien hace la petición, leídos de la base (RN-AU-02); sin caché."""
    _sin_cache(respuesta)
    return UsuarioDeLaSesionSalida.desde_usuario(usuario_de_la_sesion(actor, uow))
