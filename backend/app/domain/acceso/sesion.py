"""Reglas de la sesión del panel: claims, vigencia y token válido (RN-AU-03, design J5).

Firmar y leer el JWT es infraestructura; acá solo se decide qué token sirve. Toda fecha es
aware y la vigencia se mide con el reloj que llega por parámetro, nunca con el del sistema.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from app.domain.acceso.usuarios import DatosUsuario
from app.domain.errors import SesionInvalida
from app.domain.tiempo import exigir_utc


class TipoDeToken(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass(frozen=True)
class ClaimsDeSesion:
    usuario_id: int
    token_version: int
    tipo: TipoDeToken
    emitido_en: datetime
    vence_en: datetime

    def __post_init__(self) -> None:
        exigir_utc(self.emitido_en, "emitido_en")
        exigir_utc(self.vence_en, "vence_en")


def claims_para(
    usuario: DatosUsuario, tipo: TipoDeToken, ahora: datetime, vigencia: timedelta
) -> ClaimsDeSesion:
    return ClaimsDeSesion(
        usuario_id=usuario.id,
        token_version=usuario.token_version,
        tipo=tipo,
        emitido_en=ahora,
        vence_en=ahora + vigencia,
    )


def esta_vigente(claims: ClaimsDeSesion, ahora: datetime) -> bool:
    """Intervalo semiabierto: vale desde que se emite hasta el instante de vencer, sin incluirlo."""
    return claims.emitido_en <= ahora < claims.vence_en


def exigir_token_valido(
    claims: ClaimsDeSesion,
    tipo_esperado: TipoDeToken,
    usuario: DatosUsuario | None,
    ahora: datetime,
) -> None:
    """Levanta ``SesionInvalida`` si el token no sirve; no dice por qué (RN-AU-03, D200)."""
    if (
        claims.tipo is not tipo_esperado
        or not esta_vigente(claims, ahora)
        or usuario is None
        or not usuario.activo
        or usuario.token_version != claims.token_version
    ):
        raise SesionInvalida()
