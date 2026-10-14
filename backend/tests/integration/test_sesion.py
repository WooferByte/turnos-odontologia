"""Casos de uso de la sesión sobre SQLite en memoria, con el hasher y el firmador reales (US-090, US-094; design J8, J9)."""
from datetime import datetime, timedelta

import pytest

from app.application.sesion import IniciarSesionComando, Vigencias, iniciar_sesion
from app.domain.acceso.sesion import TipoDeToken
from app.domain.tiempo import UTC
from app.infrastructure.seguridad.contrasenas import HasherBcrypt
from app.infrastructure.seguridad.tokens import FirmadorJwtHs256
from tests.conftest import RELOJ_FIJO, SECRETO_DE_PRUEBA, reloj_fijo
from tests.factories import CONTRASENA_DE_PRUEBA, un_consultorio, un_usuario

VIGENCIAS = Vigencias(access=timedelta(minutes=15), refresh=timedelta(days=7))


@pytest.fixture
def hasher() -> HasherBcrypt:
    return HasherBcrypt(4)


@pytest.fixture
def firmador() -> FirmadorJwtHs256:
    return FirmadorJwtHs256(SECRETO_DE_PRUEBA)


def test_us090_ca1_credenciales_validas_devuelven_access_y_refresh(sesion, uow, hasher, firmador) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))

    tokens = iniciar_sesion(
        IniciarSesionComando(email=usuario.email, contrasena=CONTRASENA_DE_PRUEBA),
        uow, hasher, firmador, VIGENCIAS, reloj_fijo,
    )

    access = firmador.leer(tokens.access_token)
    refresh = firmador.leer(tokens.refresh_token)
    assert (access.tipo, access.usuario_id, access.token_version) == (TipoDeToken.ACCESS, usuario.id, 0)
    assert (refresh.tipo, refresh.usuario_id, refresh.token_version) == (TipoDeToken.REFRESH, usuario.id, 0)
    assert access.emitido_en == refresh.emitido_en == RELOJ_FIJO
    assert access.vence_en == datetime(2026, 10, 7, 12, 15, tzinfo=UTC)
    assert refresh.vence_en == datetime(2026, 10, 14, 12, 0, tzinfo=UTC)


def test_us090_ca1_email_con_mayusculas_y_espacios_inicia_sesion(sesion, uow, hasher, firmador) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))

    tokens = iniciar_sesion(
        IniciarSesionComando(email=f"  {usuario.email.upper()} ", contrasena=CONTRASENA_DE_PRUEBA),
        uow, hasher, firmador, VIGENCIAS, reloj_fijo,
    )

    assert firmador.leer(tokens.access_token).usuario_id == usuario.id
