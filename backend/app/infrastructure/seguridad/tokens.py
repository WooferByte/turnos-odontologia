"""Firmador de tokens JWT con HS256 (design J7).

PyJWT verifica la firma, el algoritmo (lista cerrada) y los claims obligatorios. El tiempo NO lo mira:
usa ``time.time()`` y la vigencia la decide el dominio con el reloj inyectado (regla dura 2).
"""
from datetime import datetime

import jwt

from app.application.puertos import TokenIlegible
from app.domain.acceso.sesion import ClaimsDeSesion, TipoDeToken
from app.domain.tiempo import UTC

MINIMO_DE_BYTES_DEL_SECRETO = 32  # RFC 7518 §3.2: clave de 256 bits como mínimo para HS256 (D198)
_CLAIMS_OBLIGATORIOS = ["sub", "typ", "token_version", "iat", "exp"]
_OPCIONES_DE_LECTURA = {
    "verify_exp": False,
    "verify_iat": False,
    "verify_nbf": False,
    "require": _CLAIMS_OBLIGATORIOS,
    "enforce_minimum_key_length": True,
}


class FirmadorJwtHs256:
    def __init__(self, secreto: str) -> None:
        if len(secreto.encode("utf-8")) < MINIMO_DE_BYTES_DEL_SECRETO:
            raise ValueError(f"El secreto de firma debe tener {MINIMO_DE_BYTES_DEL_SECRETO} bytes como mínimo.")
        self._secreto = secreto

    def firmar(self, claims: ClaimsDeSesion) -> str:
        payload = {
            "sub": str(claims.usuario_id),
            "typ": claims.tipo.value,
            "token_version": claims.token_version,
            "iat": int(claims.emitido_en.timestamp()),
            "exp": int(claims.vence_en.timestamp()),
        }
        return jwt.encode(payload, self._secreto, algorithm="HS256")

    def leer(self, token: str) -> ClaimsDeSesion:
        try:
            contenido = jwt.decode(token, self._secreto, algorithms=["HS256"], options=_OPCIONES_DE_LECTURA)
            token_version = contenido["token_version"]
            if isinstance(token_version, bool) or not isinstance(token_version, int):
                raise TokenIlegible()
            return ClaimsDeSesion(
                usuario_id=int(contenido["sub"]),
                token_version=token_version,
                tipo=TipoDeToken(contenido["typ"]),
                emitido_en=datetime.fromtimestamp(contenido["iat"], UTC),
                vence_en=datetime.fromtimestamp(contenido["exp"], UTC),
            )
        except TokenIlegible:
            raise
        except (jwt.PyJWTError, KeyError, ValueError, TypeError, OverflowError, OSError) as causa:
            raise TokenIlegible() from causa
