"""Casos de uso de la sesión del panel (US-090, US-094; RN-AU-03, RN-AU-04). Sin ``commit()`` ni SQL."""
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from app.application.puertos import FirmadorDeTokens, HasherDeContrasenas, TokenIlegible, UnidadDeTrabajo
from app.domain.acceso.sesion import TipoDeToken, claims_para, exigir_token_valido
from app.domain.acceso.roles import UsuarioDelPanel
from app.domain.acceso.usuarios import normalizar_email, validar_largo_de_contrasena
from app.domain.errors import ContrasenaActualIncorrecta, CredencialesInvalidas, SesionInvalida


@dataclass(frozen=True)
class IniciarSesionComando:
    email: str
    contrasena: str


@dataclass(frozen=True)
class TokensDeSesion:
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class AccessToken:
    access_token: str


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


def renovar_sesion(
    token: str,
    uow: UnidadDeTrabajo,
    firmador: FirmadorDeTokens,
    vigencias: Vigencias,
    reloj: Callable[[], datetime],
) -> AccessToken:
    """Un access nuevo si el refresh sirve; no hay rotación del refresh (D201). Todo rechazo es ``SesionInvalida``."""
    try:
        claims = firmador.leer(token)
    except TokenIlegible as causa:
        raise SesionInvalida() from causa
    with uow:
        usuario = uow.usuarios.obtener(claims.usuario_id)
    ahora = reloj()
    exigir_token_valido(claims, TipoDeToken.REFRESH, usuario, ahora)
    return AccessToken(
        access_token=firmador.firmar(claims_para(usuario, TipoDeToken.ACCESS, ahora, vigencias.access))
    )


def cambiar_contrasena(
    actor: UsuarioDelPanel,
    actual: str,
    nueva: str,
    uow: UnidadDeTrabajo,
    hasher: HasherDeContrasenas,
    firmador: FirmadorDeTokens,
    vigencias: Vigencias,
    reloj: Callable[[], datetime],
) -> TokensDeSesion:
    """Cambia la contraseña del propio usuario pidiendo la actual y devuelve tokens con la versión nueva.

    El largo de la nueva es validación de entrada (RN-AU-07); la actual se compara con el hash que quedó
    confirmado, con la fila bloqueada (D299). La versión sube en 1: caen todas las demás sesiones (RN-AU-03).
    """
    validar_largo_de_contrasena(nueva, "contrasena_nueva")
    # bcrypt no depende de la base: se hashea la nueva antes de abrir la transacción (V2, K10).
    hash_nuevo = hasher.hashear(nueva)
    with uow:
        usuario = uow.usuarios.obtener_para_cambiar(actor.id)
        if usuario is None:
            raise SesionInvalida()
        if not hasher.verificar(actual, usuario.hash_password):
            raise ContrasenaActualIncorrecta()
        usuario = uow.usuarios.guardar(
            replace(usuario, hash_password=hash_nuevo, token_version=usuario.token_version + 1)
        )
    ahora = reloj()
    return TokensDeSesion(
        access_token=firmador.firmar(claims_para(usuario, TipoDeToken.ACCESS, ahora, vigencias.access)),
        refresh_token=firmador.firmar(claims_para(usuario, TipoDeToken.REFRESH, ahora, vigencias.refresh)),
    )
