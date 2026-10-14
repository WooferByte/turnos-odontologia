"""``/auth``: iniciar sesión y renovarla (C-06). Endpoints síncronos (``def``, D12)."""
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_firmador, get_hasher, get_reloj, get_uow, get_vigencias
from app.api.esquemas import AccessSalida, LoginEntrada, RefreshEntrada, TokensSalida
from app.api.respuestas import _respuesta_de_error
from app.application.puertos import FirmadorDeTokens, HasherDeContrasenas, UnidadDeTrabajo
from app.application.sesion import IniciarSesionComando, Vigencias, iniciar_sesion, renovar_sesion
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
