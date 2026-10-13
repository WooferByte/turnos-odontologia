"""Lectura de DATABASE_URL del entorno (INF-4; design I11, I12)."""
import pytest

from app.infrastructure.configuracion import ConfiguracionInvalida, leer_database_url


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
