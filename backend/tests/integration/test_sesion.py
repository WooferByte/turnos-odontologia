"""Casos de uso de la sesión sobre SQLite en memoria, con el hasher y el firmador reales (US-090, US-094; design J8, J9)."""
from datetime import datetime, timedelta

import pytest

from app.application.sesion import IniciarSesionComando, Vigencias, iniciar_sesion, renovar_sesion
from app.domain.acceso.sesion import ClaimsDeSesion
from app.domain.errors import CredencialesInvalidas, SesionInvalida
from app.domain.acceso.sesion import TipoDeToken
from app.domain.tiempo import UTC
from app.infrastructure.seguridad.contrasenas import HasherBcrypt
from app.infrastructure.seguridad.tokens import FirmadorJwtHs256
from tests.conftest import RELOJ_FIJO, SECRETO_DE_PRUEBA, reloj_fijo
from tests.factories import CONTRASENA_DE_PRUEBA, un_consultorio, un_usuario

VIGENCIAS = Vigencias(access=timedelta(minutes=15), refresh=timedelta(days=7))


class HasherQueCuenta:
    """Envoltorio sobre el hasher real que cuenta las comparaciones; no reemplaza ningún comportamiento (design J17)."""

    def __init__(self, real: HasherBcrypt) -> None:
        self._real = real
        self.comparaciones = 0

    def hashear(self, contrasena: str) -> str:
        return self._real.hashear(contrasena)

    def verificar(self, contrasena: str, hash_guardado: str) -> bool:
        self.comparaciones += 1
        return self._real.verificar(contrasena, hash_guardado)

    def verificar_sin_usuario(self, contrasena: str) -> bool:
        self.comparaciones += 1
        return self._real.verificar_sin_usuario(contrasena)


def _iniciar(uow, hasher, firmador, email: str, contrasena: str):
    return iniciar_sesion(
        IniciarSesionComando(email=email, contrasena=contrasena),
        uow, hasher, firmador, VIGENCIAS, reloj_fijo,
    )


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


def test_us090_ca2_email_inexistente_rechaza_con_rn_au_04(sesion, uow, hasher, firmador) -> None:
    un_usuario(sesion, un_consultorio(sesion))

    with pytest.raises(CredencialesInvalidas) as excinfo:
        _iniciar(uow, hasher, firmador, "nadie@consultorio-demo.test", CONTRASENA_DE_PRUEBA)

    assert excinfo.value.codigos == ["RN-AU-04"]


def test_us090_ca2_contrasena_incorrecta_rechaza_con_rn_au_04(sesion, uow, hasher, firmador) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))

    with pytest.raises(CredencialesInvalidas) as excinfo:
        _iniciar(uow, hasher, firmador, usuario.email, "otra-contrasena-ficticia")

    assert excinfo.value.codigos == ["RN-AU-04"]


def test_us090_ca2_contrasena_de_73_bytes_rechaza_sin_error(sesion, uow, hasher, firmador) -> None:
    larga = "a" * 72 + "b"
    usuario = un_usuario(sesion, un_consultorio(sesion), contrasena="a" * 72)

    with pytest.raises(CredencialesInvalidas):
        _iniciar(uow, hasher, firmador, usuario.email, larga)


@pytest.mark.parametrize("caso", ["email_inexistente", "contrasena_incorrecta", "inactivo"])
def test_us090_ca2_siempre_se_compara_una_contrasena(sesion, uow, firmador, caso) -> None:
    contador = HasherQueCuenta(HasherBcrypt(4))
    usuario = un_usuario(sesion, un_consultorio(sesion), activo=caso != "inactivo")
    email = "nadie@consultorio-demo.test" if caso == "email_inexistente" else usuario.email
    contrasena = "otra-contrasena-ficticia" if caso == "contrasena_incorrecta" else CONTRASENA_DE_PRUEBA

    with pytest.raises(CredencialesInvalidas):
        _iniciar(uow, contador, firmador, email, contrasena)

    assert contador.comparaciones == 1


@pytest.mark.parametrize("contrasena", [CONTRASENA_DE_PRUEBA, "otra-contrasena-ficticia"], ids=["correcta", "incorrecta"])
def test_us090_ca3_usuario_inactivo_rechaza_con_rn_au_04(sesion, uow, hasher, firmador, contrasena) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion), activo=False)

    with pytest.raises(CredencialesInvalidas) as excinfo:
        _iniciar(uow, hasher, firmador, usuario.email, contrasena)

    assert excinfo.value.codigos == ["RN-AU-04"]


def _reloj_en(instante: datetime):
    return lambda: instante


def test_us094_ca1_refresh_valido_devuelve_un_access_nuevo(sesion, uow, hasher, firmador) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion), token_version=3)
    tokens = _iniciar(uow, hasher, firmador, usuario.email, CONTRASENA_DE_PRUEBA)
    una_hora_despues = RELOJ_FIJO + timedelta(hours=1)

    nuevo = renovar_sesion(tokens.refresh_token, uow, firmador, VIGENCIAS, _reloj_en(una_hora_despues))

    claims = firmador.leer(nuevo.access_token)
    assert (claims.tipo, claims.usuario_id, claims.token_version) == (TipoDeToken.ACCESS, usuario.id, 3)
    assert claims.emitido_en == una_hora_despues
    assert claims.vence_en == datetime(2026, 10, 7, 13, 15, tzinfo=UTC)
    assert not hasattr(nuevo, "refresh_token")


def test_us094_ca1_un_segundo_antes_de_vencer_sigue_sirviendo(sesion, uow, hasher, firmador) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))
    tokens = _iniciar(uow, hasher, firmador, usuario.email, CONTRASENA_DE_PRUEBA)
    antes_de_vencer = RELOJ_FIJO + VIGENCIAS.refresh - timedelta(seconds=1)

    nuevo = renovar_sesion(tokens.refresh_token, uow, firmador, VIGENCIAS, _reloj_en(antes_de_vencer))

    assert firmador.leer(nuevo.access_token).emitido_en == antes_de_vencer


def _renovar(uow, firmador, token: str, ahora: datetime = RELOJ_FIJO + timedelta(hours=1)):
    return renovar_sesion(token, uow, firmador, VIGENCIAS, _reloj_en(ahora))


def _alterar_la_firma(token: str) -> str:
    encabezado, contenido, firma = token.split(".")
    medio = len(firma) // 2
    cambiado = "A" if firma[medio] != "A" else "B"
    return ".".join([encabezado, contenido, firma[:medio] + cambiado + firma[medio + 1:]])


def test_us094_ca2_refresh_vencido_en_el_instante_exacto(sesion, uow, hasher, firmador) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))
    tokens = _iniciar(uow, hasher, firmador, usuario.email, CONTRASENA_DE_PRUEBA)

    with pytest.raises(SesionInvalida) as excinfo:
        _renovar(uow, firmador, tokens.refresh_token, RELOJ_FIJO + VIGENCIAS.refresh)

    assert excinfo.value.codigos == ["RN-AU-03"]


@pytest.mark.parametrize("como", ["otro_secreto", "firma_alterada"])
def test_us094_ca2_refresh_de_otro_secreto_o_alterado(sesion, uow, hasher, firmador, como) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))
    tokens = _iniciar(uow, hasher, firmador, usuario.email, CONTRASENA_DE_PRUEBA)
    if como == "otro_secreto":
        claims = firmador.leer(tokens.refresh_token)
        token = FirmadorJwtHs256("otro-secreto-ficticio-de-mas-de-32-bytes-0123").firmar(claims)
    else:
        token = _alterar_la_firma(tokens.refresh_token)

    with pytest.raises(SesionInvalida):
        _renovar(uow, firmador, token)


def test_us094_ca2_access_token_no_sirve_como_refresh(sesion, uow, hasher, firmador) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))
    tokens = _iniciar(uow, hasher, firmador, usuario.email, CONTRASENA_DE_PRUEBA)

    with pytest.raises(SesionInvalida):
        _renovar(uow, firmador, tokens.access_token, RELOJ_FIJO)


def test_us094_ca2_texto_que_no_es_jwt(uow, firmador) -> None:
    with pytest.raises(SesionInvalida) as excinfo:
        _renovar(uow, firmador, "abc")

    assert excinfo.value.codigos == ["RN-AU-03"]


def test_us094_ca3_usuario_desactivado_despues_del_login(sesion, uow, hasher, firmador) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))
    tokens = _iniciar(uow, hasher, firmador, usuario.email, CONTRASENA_DE_PRUEBA)
    usuario.activo = False
    sesion.commit()

    with pytest.raises(SesionInvalida):
        _renovar(uow, firmador, tokens.refresh_token)


def test_us094_ca3_token_version_cambiada(sesion, uow, hasher, firmador) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))
    tokens = _iniciar(uow, hasher, firmador, usuario.email, CONTRASENA_DE_PRUEBA)
    usuario.token_version += 1
    sesion.commit()

    with pytest.raises(SesionInvalida):
        _renovar(uow, firmador, tokens.refresh_token)


def test_us094_ca3_reactivado_no_revive_el_token_viejo(sesion, uow, hasher, firmador) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))
    viejos = _iniciar(uow, hasher, firmador, usuario.email, CONTRASENA_DE_PRUEBA)
    usuario.activo = False
    sesion.commit()
    usuario.activo = True
    usuario.token_version += 1
    sesion.commit()

    with pytest.raises(SesionInvalida):
        _renovar(uow, firmador, viejos.refresh_token)
    nuevos = _iniciar(uow, hasher, firmador, usuario.email, CONTRASENA_DE_PRUEBA)
    renovado = _renovar(uow, firmador, nuevos.refresh_token)
    assert firmador.leer(renovado.access_token).token_version == 1


def test_us094_ca3_usuario_inexistente(sesion, uow, firmador) -> None:
    un_consultorio(sesion)
    claims = ClaimsDeSesion(
        usuario_id=999, token_version=0, tipo=TipoDeToken.REFRESH,
        emitido_en=RELOJ_FIJO, vence_en=RELOJ_FIJO + VIGENCIAS.refresh,
    )

    with pytest.raises(SesionInvalida):
        _renovar(uow, firmador, firmador.firmar(claims))
