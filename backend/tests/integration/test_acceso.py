"""Identificar y autorizar al usuario de cada petición, con SQLite real, el firmador real y el reloj fijo.

US-092 CA-1 y CA-4, US-091 CA-1, CA-3 y CA-5; RN-AU-01 a RN-AU-05 (design R8).
"""
from datetime import datetime, timedelta

import pytest

from app.application.acceso import identificar_usuario
from app.application.sesion import IniciarSesionComando, Vigencias, iniciar_sesion
from app.domain.acceso.roles import Rol, UsuarioDelPanel
from app.domain.acceso.sesion import ClaimsDeSesion, TipoDeToken, claims_para
from app.domain.errors import SesionInvalida
from app.domain.tiempo import UTC
from app.infrastructure.seguridad.contrasenas import HasherBcrypt
from app.infrastructure.seguridad.tokens import FirmadorJwtHs256
from tests.conftest import RELOJ_FIJO, SECRETO_DE_PRUEBA, reloj_fijo
from tests.factories import CONTRASENA_DE_PRUEBA, un_consultorio, un_usuario

VIGENCIAS = Vigencias(access=timedelta(minutes=15), refresh=timedelta(days=7))


def _reloj_en(instante: datetime):
    return lambda: instante


def _a_las(hora: int, minuto: int = 0, segundo: int = 0) -> datetime:
    return datetime(2026, 10, 7, hora, minuto, segundo, tzinfo=UTC)


@pytest.fixture
def firmador() -> FirmadorJwtHs256:
    return FirmadorJwtHs256(SECRETO_DE_PRUEBA)


@pytest.fixture
def consultorio(sesion):
    return un_consultorio(sesion)


def _iniciar_sesion(uow, firmador, usuario):
    """Login real a las 12:00 (el reloj fijo): devuelve los dos tokens."""
    return iniciar_sesion(
        IniciarSesionComando(email=usuario.email, contrasena=CONTRASENA_DE_PRUEBA),
        uow, HasherBcrypt(4), firmador, VIGENCIAS, reloj_fijo,
    )


def test_us092_ca1_access_vigente_identifica_al_usuario_con_sus_roles(sesion, uow, firmador, consultorio) -> None:
    usuario = un_usuario(sesion, consultorio, roles=(Rol.ODONTOLOGO, Rol.DUENO))
    tokens = _iniciar_sesion(uow, firmador, usuario)

    identificado = identificar_usuario(tokens.access_token, uow, firmador, _reloj_en(_a_las(12, 14, 59)))

    assert identificado == UsuarioDelPanel(id=usuario.id, roles=frozenset({Rol.ODONTOLOGO, Rol.DUENO}))


def test_us092_ca1_sin_token_es_sesion_invalida(uow, firmador) -> None:
    with pytest.raises(SesionInvalida) as error:
        identificar_usuario(None, uow, firmador, reloj_fijo)

    assert error.value.codigos == ["RN-AU-03"]


def test_us092_ca1_access_vencido_en_el_instante_exacto(sesion, uow, firmador, consultorio) -> None:
    usuario = un_usuario(sesion, consultorio, roles=(Rol.ODONTOLOGO,))
    tokens = _iniciar_sesion(uow, firmador, usuario)

    with pytest.raises(SesionInvalida) as error:
        identificar_usuario(tokens.access_token, uow, firmador, _reloj_en(_a_las(12, 15)))

    assert error.value.codigos == ["RN-AU-03"]


def test_us092_ca1_refresh_no_sirve_como_access(sesion, uow, firmador, consultorio) -> None:
    usuario = un_usuario(sesion, consultorio, roles=(Rol.ODONTOLOGO,))
    tokens = _iniciar_sesion(uow, firmador, usuario)

    with pytest.raises(SesionInvalida) as error:
        identificar_usuario(tokens.refresh_token, uow, firmador, reloj_fijo)

    assert error.value.codigos == ["RN-AU-03"]


def _token_ilegible(caso: str, sesion, uow, firmador, usuario) -> str:
    valido = _iniciar_sesion(uow, firmador, usuario).access_token
    if caso == "texto cualquiera":
        return "esto-no-es-un-token"
    if caso == "otro secreto":
        claims = claims_para(usuario_de_dominio(uow, usuario.id), TipoDeToken.ACCESS, RELOJ_FIJO, VIGENCIAS.access)
        return FirmadorJwtHs256("otro-secreto-ficticio-de-mas-de-32-bytes-0123456789").firmar(claims)
    cabecera, cuerpo, firma = valido.split(".")  # firma alterada
    alterada = ("A" if firma[3] != "A" else "B").join([firma[:3], firma[4:]])
    return ".".join([cabecera, cuerpo, alterada])


def usuario_de_dominio(uow, usuario_id: int):
    with uow:
        return uow.usuarios.obtener(usuario_id)


@pytest.mark.parametrize("caso", ["texto cualquiera", "otro secreto", "firma alterada"])
def test_us092_ca1_token_ilegible_o_de_otro_secreto(caso, sesion, uow, firmador, consultorio) -> None:
    usuario = un_usuario(sesion, consultorio, roles=(Rol.ODONTOLOGO,))
    token = _token_ilegible(caso, sesion, uow, firmador, usuario)

    with pytest.raises(SesionInvalida) as error:
        identificar_usuario(token, uow, firmador, reloj_fijo)

    assert error.value.codigos == ["RN-AU-03"]


def test_us092_ca4_usuario_desactivado_despues_del_login(sesion, uow, firmador, consultorio) -> None:
    usuario = un_usuario(sesion, consultorio, roles=(Rol.ODONTOLOGO,))
    tokens = _iniciar_sesion(uow, firmador, usuario)
    usuario.activo = False
    sesion.commit()

    with pytest.raises(SesionInvalida) as error:
        identificar_usuario(tokens.access_token, uow, firmador, reloj_fijo)

    assert error.value.codigos == ["RN-AU-03"]


def test_us092_ca4_token_version_cambiada(sesion, uow, firmador, consultorio) -> None:
    usuario = un_usuario(sesion, consultorio, roles=(Rol.ODONTOLOGO,))
    tokens = _iniciar_sesion(uow, firmador, usuario)
    usuario.token_version += 1
    sesion.commit()

    with pytest.raises(SesionInvalida):
        identificar_usuario(tokens.access_token, uow, firmador, reloj_fijo)


def test_us092_ca4_reactivado_no_revive_el_token_viejo(sesion, uow, firmador, consultorio) -> None:
    usuario = un_usuario(sesion, consultorio, roles=(Rol.ODONTOLOGO,))
    viejo = _iniciar_sesion(uow, firmador, usuario).access_token
    usuario.activo, usuario.token_version = False, usuario.token_version + 1  # desactivar sube la versión
    sesion.commit()
    usuario.activo = True
    sesion.commit()

    with pytest.raises(SesionInvalida):
        identificar_usuario(viejo, uow, firmador, reloj_fijo)

    nuevo = _iniciar_sesion(uow, firmador, usuario).access_token
    assert firmador.leer(nuevo).token_version == 1
    assert identificar_usuario(nuevo, uow, firmador, reloj_fijo).id == usuario.id


def test_us092_ca4_usuario_inexistente(uow, firmador) -> None:
    claims = ClaimsDeSesion(
        usuario_id=999,
        token_version=0,
        tipo=TipoDeToken.ACCESS,
        emitido_en=RELOJ_FIJO,
        vence_en=RELOJ_FIJO + VIGENCIAS.access,
    )

    with pytest.raises(SesionInvalida) as error:
        identificar_usuario(firmador.firmar(claims), uow, firmador, reloj_fijo)

    assert error.value.codigos == ["RN-AU-03"]
