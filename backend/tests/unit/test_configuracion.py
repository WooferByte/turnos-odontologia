"""Lectura de DATABASE_URL del entorno (INF-4; design I11, I12)."""
import pytest

from app.infrastructure.configuracion import (
    ConfiguracionDeSesion,
    ConfiguracionInvalida,
    leer_configuracion_de_sesion,
    leer_database_url,
    secreto_efimero,
)


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://app:app@postgres:5432/turnos",
        "postgresql+psycopg://otro:clave@127.0.0.1:5434/otra_base",
    ],
)
def test_leer_database_url_devuelve_el_valor_del_entorno_dado(url: str) -> None:
    entorno = {"DATABASE_URL": url, "OTRA": "ignorada"}

    assert leer_database_url(entorno) == url


def test_leer_database_url_sin_la_variable_levanta_error_que_la_nombra() -> None:
    with pytest.raises(ConfiguracionInvalida, match="DATABASE_URL"):
        leer_database_url({"OTRA": "x"})


def test_leer_database_url_vacia_levanta_error_que_la_nombra() -> None:
    with pytest.raises(ConfiguracionInvalida, match="DATABASE_URL"):
        leer_database_url({"DATABASE_URL": ""})


# --- Sesión del panel (C-06; design J10) ---

SECRETO_32 = "s" * 32


def test_sesion_con_secreto_de_32_bytes_usa_15_minutos_y_7_dias_por_defecto() -> None:
    config = leer_configuracion_de_sesion({"JWT_SECRET": SECRETO_32})

    assert config == ConfiguracionDeSesion(SECRETO_32, minutos_access=15, dias_refresh=7, rondas_bcrypt=12)


def test_sesion_lee_minutos_y_dias_del_entorno() -> None:
    entorno = {"JWT_SECRET": SECRETO_32, "JWT_ACCESS_MINUTES": "30", "JWT_REFRESH_DAYS": "1"}

    config = leer_configuracion_de_sesion(entorno)

    assert (config.minutos_access, config.dias_refresh) == (30, 1)


@pytest.mark.parametrize("entorno", [{}, {"JWT_SECRET": ""}, {"JWT_SECRET": "s" * 31}], ids=["ausente", "vacia", "31_bytes"])
def test_sesion_con_secreto_ausente_vacio_o_corto_levanta_error_que_nombra_la_variable(entorno) -> None:
    with pytest.raises(ConfiguracionInvalida, match="JWT_SECRET") as error:
        leer_configuracion_de_sesion(entorno)

    assert "s" * 31 not in str(error.value)


def test_sesion_cuenta_los_bytes_y_no_los_caracteres_del_secreto() -> None:
    secreto = "ñ" * 16  # 16 caracteres, 32 bytes en UTF-8

    assert leer_configuracion_de_sesion({"JWT_SECRET": secreto}).secreto == secreto


@pytest.mark.parametrize("variable", ["JWT_ACCESS_MINUTES", "JWT_REFRESH_DAYS"])
@pytest.mark.parametrize("valor", ["0", "-1", "abc", ""])
def test_sesion_con_vigencia_invalida_levanta_error_que_nombra_la_variable_y_no_su_valor(variable, valor) -> None:
    entorno = {"JWT_SECRET": SECRETO_32, variable: valor}

    with pytest.raises(ConfiguracionInvalida, match=variable) as error:
        leer_configuracion_de_sesion(entorno)

    if valor == "abc":
        assert valor not in str(error.value)


def test_sesion_repr_no_muestra_el_secreto() -> None:
    config = ConfiguracionDeSesion("secreto-que-no-debe-aparecer-en-el-repr-0000")

    assert "secreto-que-no-debe-aparecer" not in repr(config)


def test_secreto_efimero_cumple_el_minimo_y_cambia_cada_vez() -> None:
    primero, segundo = secreto_efimero(), secreto_efimero()

    assert len(primero.encode()) >= 32
    assert primero != segundo
