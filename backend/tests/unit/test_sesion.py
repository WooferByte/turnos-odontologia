"""Reglas de la sesión del panel en el dominio: claims, vigencia y token válido (US-090, US-094; RN-AU-03, RN-AU-04)."""
from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from app.domain.acceso.sesion import (
    ClaimsDeSesion,
    TipoDeToken,
    claims_para,
    esta_vigente,
    exigir_token_valido,
)
from app.domain.acceso.usuarios import DatosUsuario, normalizar_email
from app.domain.errors import SesionInvalida
from app.domain.tiempo import UTC

LAS_12 = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)
QUINCE_MINUTOS = timedelta(minutes=15)
SIETE_DIAS = timedelta(days=7)


def un_usuario_de_dominio(**cambios) -> DatosUsuario:
    base = DatosUsuario(
        id=1,
        consultorio_id=1,
        email="odontologa@consultorio-demo.test",
        hash_password="$2b$04$hash-ficticio",
        activo=True,
        token_version=0,
        creado_en=LAS_12,
    )
    return replace(base, **cambios)


def test_us090_ca4_claims_de_access_vencen_a_los_15_minutos() -> None:
    claims = claims_para(un_usuario_de_dominio(), TipoDeToken.ACCESS, LAS_12, QUINCE_MINUTOS)

    assert claims == ClaimsDeSesion(
        usuario_id=1,
        token_version=0,
        tipo=TipoDeToken.ACCESS,
        emitido_en=LAS_12,
        vence_en=datetime(2026, 10, 7, 12, 15, tzinfo=UTC),
    )


def test_us090_ca4_claims_de_refresh_vencen_a_los_7_dias() -> None:
    usuario = un_usuario_de_dominio(token_version=3)

    claims = claims_para(usuario, TipoDeToken.REFRESH, LAS_12, SIETE_DIAS)

    assert claims.tipo is TipoDeToken.REFRESH
    assert claims.token_version == 3
    assert claims.vence_en == datetime(2026, 10, 14, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("ahora", "vigente"),
    [
        (LAS_12, True),
        (LAS_12 + QUINCE_MINUTOS - timedelta(seconds=1), True),
        (LAS_12 + QUINCE_MINUTOS, False),
        (LAS_12 + QUINCE_MINUTOS + timedelta(seconds=1), False),
    ],
)
def test_us094_ca2_vigencia_semiabierta(ahora: datetime, vigente: bool) -> None:
    claims = claims_para(un_usuario_de_dominio(), TipoDeToken.ACCESS, LAS_12, QUINCE_MINUTOS)

    assert esta_vigente(claims, ahora) is vigente


@pytest.mark.parametrize(
    ("usuario", "tipo_esperado"),
    [
        (None, TipoDeToken.REFRESH),
        (un_usuario_de_dominio(activo=False), TipoDeToken.REFRESH),
        (un_usuario_de_dominio(token_version=1), TipoDeToken.REFRESH),
        (un_usuario_de_dominio(), TipoDeToken.ACCESS),
    ],
    ids=["usuario_ausente", "usuario_inactivo", "token_version_distinta", "tipo_distinto"],
)
def test_us094_ca3_token_valido_exige_usuario_activo_y_misma_version(
    usuario: DatosUsuario | None, tipo_esperado: TipoDeToken
) -> None:
    claims = claims_para(un_usuario_de_dominio(), TipoDeToken.REFRESH, LAS_12, SIETE_DIAS)

    with pytest.raises(SesionInvalida) as error:
        exigir_token_valido(claims, tipo_esperado, usuario, LAS_12)

    assert error.value.codigos == ["RN-AU-03"]


def test_us090_ca1_normalizar_email() -> None:
    assert normalizar_email(" Odontologa@Consultorio-Demo.TEST ") == "odontologa@consultorio-demo.test"
