"""Adaptadores de seguridad: hasher bcrypt y firmador JWT HS256 (US-090 CA-2 y CA-4, US-094 CA-2; design J6, J7)."""
from datetime import datetime, timedelta

import jwt
import pytest

from app.application.puertos import TokenIlegible
from app.domain.acceso.sesion import ClaimsDeSesion, TipoDeToken
from app.domain.tiempo import UTC
from app.infrastructure.seguridad.contrasenas import HasherBcrypt
from app.infrastructure.seguridad.tokens import FirmadorJwtHs256
from tests.conftest import SECRETO_DE_PRUEBA

CONTRASENA = "contrasena-ficticia-1"
LAS_12 = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)
CLAIMS = ClaimsDeSesion(
    usuario_id=7,
    token_version=2,
    tipo=TipoDeToken.REFRESH,
    emitido_en=LAS_12,
    vence_en=LAS_12 + timedelta(days=7),
)
PAYLOAD_VALIDO = {
    "sub": "7",
    "typ": "access",
    "token_version": 2,
    "iat": int(LAS_12.timestamp()),
    "exp": int((LAS_12 + timedelta(minutes=15)).timestamp()),
}


# --- Hasher ---
def test_us090_ca4_el_hash_no_es_la_contrasena_y_usa_bcrypt_con_las_rondas_dadas() -> None:
    hash_ = HasherBcrypt(4).hashear(CONTRASENA)

    assert hash_ != CONTRASENA
    assert hash_.startswith("$2b$04$")


def test_us090_ca2_verifica_la_correcta_y_rechaza_la_incorrecta() -> None:
    hasher = HasherBcrypt(4)
    hash_ = hasher.hashear(CONTRASENA)

    assert hasher.verificar(CONTRASENA, hash_) is True
    assert hasher.verificar(CONTRASENA + "x", hash_) is False


@pytest.mark.parametrize("contrasena", ["a" * 72 + "b", "ñ" * 37], ids=["73_ascii", "74_utf8"])
def test_us090_ca2_mas_de_72_bytes_da_false_sin_excepcion(contrasena: str) -> None:
    hasher = HasherBcrypt(4)
    hash_ = hasher.hashear(contrasena.encode()[:72].decode("utf-8", errors="ignore"))

    assert hasher.verificar(contrasena, hash_) is False


def test_us090_ca2_verificar_sin_usuario_siempre_da_false() -> None:
    hasher = HasherBcrypt(4)

    assert hasher.verificar_sin_usuario(CONTRASENA) is False


# --- Firmador ---
def test_firmador_ida_y_vuelta_de_los_claims() -> None:
    firmador = FirmadorJwtHs256(SECRETO_DE_PRUEBA)

    assert firmador.leer(firmador.firmar(CLAIMS)) == CLAIMS


def test_firmador_usa_hs256_y_los_claims_del_design() -> None:
    token = FirmadorJwtHs256(SECRETO_DE_PRUEBA).firmar(CLAIMS)

    cabecera = jwt.get_unverified_header(token)
    contenido = jwt.decode(token, options={"verify_signature": False})
    assert cabecera["alg"] == "HS256"
    assert contenido == {
        "sub": "7",
        "typ": "refresh",
        "token_version": 2,
        "iat": int(LAS_12.timestamp()),
        "exp": int((LAS_12 + timedelta(days=7)).timestamp()),
    }


def _token_de(payload: dict, secreto: str = SECRETO_DE_PRUEBA, algoritmo: str = "HS256") -> str:
    return jwt.encode(payload, secreto, algorithm=algoritmo)


def _sin(campo: str) -> dict:
    return {k: v for k, v in PAYLOAD_VALIDO.items() if k != campo}


def _con_firma_ajena() -> str:
    cabecera, contenido, _ = _token_de(PAYLOAD_VALIDO).split(".")
    ajena = _token_de({**PAYLOAD_VALIDO, "sub": "8"}).split(".")[2]
    return f"{cabecera}.{contenido}.{ajena}"


def _con_contenido_alterado() -> str:
    cabecera, _, firma = _token_de(PAYLOAD_VALIDO).split(".")
    otro = _token_de({**PAYLOAD_VALIDO, "sub": "8"}).split(".")[1]
    return f"{cabecera}.{otro}.{firma}"


@pytest.mark.parametrize(
    "token",
    [
        _token_de(PAYLOAD_VALIDO, secreto="otro-secreto-ficticio-de-32-bytes-o-mas-xyz"),
        _con_firma_ajena(),
        _con_contenido_alterado(),
        jwt.encode(PAYLOAD_VALIDO, None, algorithm="none"),
        _token_de(PAYLOAD_VALIDO, algoritmo="HS512"),
        _token_de(_sin("token_version")),
        _token_de(_sin("typ")),
        _token_de({**PAYLOAD_VALIDO, "sub": "abc"}),
        _token_de({**PAYLOAD_VALIDO, "typ": "desconocido"}),
        "esto no es un jwt",
        "",
    ],
    ids=[
        "otro_secreto", "firma_ajena", "contenido_alterado", "alg_none", "hs512",
        "sin_token_version", "sin_typ", "sub_no_entero", "typ_desconocido", "texto_cualquiera", "vacio",
    ],
)
def test_us094_ca2_token_ilegible(token: str) -> None:
    with pytest.raises(TokenIlegible):
        FirmadorJwtHs256(SECRETO_DE_PRUEBA).leer(token)


def test_firmador_no_mira_el_tiempo_lo_decide_el_dominio() -> None:
    vencido_hace_mucho = {**PAYLOAD_VALIDO, "iat": 1, "exp": 2}
    futuro_lejano = {**PAYLOAD_VALIDO, "iat": 4102444800, "exp": 4102444900}
    firmador = FirmadorJwtHs256(SECRETO_DE_PRUEBA)

    assert firmador.leer(_token_de(vencido_hace_mucho)).vence_en == datetime(1970, 1, 1, 0, 0, 2, tzinfo=UTC)
    assert firmador.leer(_token_de(futuro_lejano)).tipo is TipoDeToken.ACCESS


def test_firmador_rechaza_un_secreto_de_31_bytes() -> None:
    with pytest.raises(ValueError):
        FirmadorJwtHs256("s" * 31)


def test_firmador_acepta_un_secreto_de_32_bytes() -> None:
    firmador = FirmadorJwtHs256("s" * 32)

    assert firmador.leer(firmador.firmar(CLAIMS)) == CLAIMS
