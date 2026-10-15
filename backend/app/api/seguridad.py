"""Dependencias de seguridad de las rutas del panel (design R9, R11).

``usuario_actual`` identifica al usuario del access token en cada petición y ``requiere`` lo
autoriza para un permiso. Toda ruta del panel pasa por ``requiere``; solo ``/auth/login`` y
``/auth/refresh`` son públicas (el guard de ``tests/api/test_proteccion_de_rutas.py`` lo exige).
"""
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.deps import get_firmador, get_reloj, get_uow
from app.application.acceso import autorizar, identificar_usuario
from app.application.puertos import FirmadorDeTokens, UnidadDeTrabajo
from app.domain.acceso.roles import Permiso, UsuarioDelPanel
from app.domain.tiempo import Reloj

# auto_error=False es obligatorio: con True, FastAPI responde 403 sin cabecera (RN-AU-05 pide 401,
# con el cuerpo problem+json). Sin cabecera o con otro esquema devuelve None y el caso de uso rechaza.
esquema_bearer = HTTPBearer(
    auto_error=False,
    scheme_name="AccessToken",
    bearerFormat="JWT",
    description="Access token de `POST /auth/login`, pegado sin el prefijo `Bearer`.",
)


def usuario_actual(
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(esquema_bearer)],
    uow: Annotated[UnidadDeTrabajo, Depends(get_uow)],
    firmador: Annotated[FirmadorDeTokens, Depends(get_firmador)],
    reloj: Annotated[Reloj, Depends(get_reloj)],
) -> UsuarioDelPanel:
    """El usuario y los roles de ahora; cualquier causa de rechazo es el mismo ``401`` (D206)."""
    token = credenciales.credentials if credenciales else None
    return identificar_usuario(token, uow, firmador, reloj)


def requiere(permiso: Permiso) -> Callable[..., UsuarioDelPanel]:
    """Dependencia que deja pasar solo a quien tiene ``permiso``; si no, ``403`` con RN-AU-05."""

    def dependencia(usuario: Annotated[UsuarioDelPanel, Depends(usuario_actual)]) -> UsuarioDelPanel:
        return autorizar(usuario, permiso)

    return dependencia
