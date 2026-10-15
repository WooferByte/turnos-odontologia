"""Casos de uso del acceso al panel: identificar al usuario de cada petición y autorizarlo (design R8).

RN-AU-01, RN-AU-02, RN-AU-03, RN-AU-04, RN-AU-05. Sin ``commit()`` ni SQL. Los roles, ``activo`` y
``token_version`` se leen de la base en cada petición: no se guardan entre una y otra (D102).
"""
from collections.abc import Callable
from datetime import datetime

from app.application.puertos import FirmadorDeTokens, TokenIlegible, UnidadDeTrabajo
from app.domain.acceso.roles import Permiso, UsuarioDelPanel, exigir_permiso
from app.domain.acceso.sesion import TipoDeToken, exigir_token_valido
from app.domain.errors import SesionInvalida


def identificar_usuario(
    token: str | None,
    uow: UnidadDeTrabajo,
    firmador: FirmadorDeTokens,
    reloj: Callable[[], datetime],
) -> UsuarioDelPanel:
    """El usuario del access token y sus roles de ahora; toda causa de rechazo es ``SesionInvalida`` (D206)."""
    if token is None:
        raise SesionInvalida()
    try:
        claims = firmador.leer(token)
    except TokenIlegible as causa:
        raise SesionInvalida() from causa
    with uow:
        usuario = uow.usuarios.obtener(claims.usuario_id)
        roles = frozenset() if usuario is None else uow.usuarios.roles_de(usuario.id)
    exigir_token_valido(claims, TipoDeToken.ACCESS, usuario, reloj())
    return UsuarioDelPanel(id=usuario.id, roles=roles)


def autorizar(usuario: UsuarioDelPanel, permiso: Permiso) -> UsuarioDelPanel:
    """Devuelve al usuario si alguno de sus roles tiene el permiso; si no, ``PermisoInsuficiente`` (RN-AU-05)."""
    exigir_permiso(usuario.roles, permiso)
    return usuario
