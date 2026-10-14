"""``crear_app_desde_entorno`` no cae en silencio a otra base (design I11, I12)."""
import pytest

from app.infrastructure.configuracion import ConfiguracionInvalida
from app.main import crear_app_desde_entorno
from tests.conftest import SECRETO_DE_PRUEBA

URL_DE_PRUEBA = "sqlite+pysqlite:///:memory:"


def test_crear_app_desde_entorno_sin_database_url_falla():
    with pytest.raises(ConfiguracionInvalida, match="DATABASE_URL"):
        crear_app_desde_entorno({})


def test_crear_app_desde_entorno_con_database_url_vacia_falla():
    with pytest.raises(ConfiguracionInvalida, match="DATABASE_URL"):
        crear_app_desde_entorno({"DATABASE_URL": ""})


@pytest.mark.parametrize(
    "secreto",
    [pytest.param(None, id="ausente"), "", "a" * 31],
)
def test_crear_app_desde_entorno_sin_jwt_secret_valido_falla_nombrandolo(secreto):
    entorno = {"DATABASE_URL": URL_DE_PRUEBA}
    if secreto is not None:
        entorno["JWT_SECRET"] = secreto

    with pytest.raises(ConfiguracionInvalida, match="JWT_SECRET") as error:
        crear_app_desde_entorno(entorno)

    if secreto:
        assert secreto not in str(error.value)


def test_crear_app_desde_entorno_con_jwt_secret_de_32_bytes_arranca():
    app = crear_app_desde_entorno({"DATABASE_URL": URL_DE_PRUEBA, "JWT_SECRET": SECRETO_DE_PRUEBA})

    assert app.title == "Turnos Odontológicos AR"
