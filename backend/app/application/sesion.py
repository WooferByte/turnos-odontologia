"""Casos de uso de la sesión del panel (US-090, US-094; RN-AU-03, RN-AU-04). Sin ``commit()`` ni SQL."""
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.application.puertos import FirmadorDeTokens, HasherDeContrasenas, UnidadDeTrabajo
from app.domain.acceso.sesion import TipoDeToken, claims_para
from app.domain.acceso.usuarios import normalizar_email
from app.domain.errors import CredencialesInvalidas


@dataclass(frozen=True)
class IniciarSesionComando:
    email: str
    contrasena: str


@dataclass(frozen=True)
class TokensDeSesion:
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class Vigencias:
    access: timedelta
    refresh: timedelta


def iniciar_sesion(
    comando: IniciarSesionComando,
    uow: UnidadDeTrabajo,
    hasher: HasherDeContrasenas,
    firmador: FirmadorDeTokens,
    vigencias: Vigencias,
    reloj: Callable[[], datetime],
) -> TokensDeSesion:
    """Todos los rechazos salen como ``CredencialesInvalidas`` y cuestan una comparación de bcrypt (design J8)."""
    with uow:
        usuario = uow.usuarios.por_email(normalizar_email(comando.email))
    if usuario is None:
        hasher.verificar_sin_usuario(comando.contrasena)
        raise CredencialesInvalidas()
    coincide = hasher.verificar(comando.contrasena, usuario.hash_password)
    if not coincide or not usuario.activo:
        raise CredencialesInvalidas()
    ahora = reloj()
    return TokensDeSesion(
        access_token=firmador.firmar(claims_para(usuario, TipoDeToken.ACCESS, ahora, vigencias.access)),
        refresh_token=firmador.firmar(claims_para(usuario, TipoDeToken.REFRESH, ahora, vigencias.refresh)),
    )
