"""``crear_app_desde_entorno`` no cae en silencio a otra base (design I11, I12)."""
import pytest

from app.infrastructure.configuracion import ConfiguracionInvalida
from app.main import crear_app_desde_entorno


def test_crear_app_desde_entorno_sin_database_url_falla():
    with pytest.raises(ConfiguracionInvalida, match="DATABASE_URL"):
        crear_app_desde_entorno({})


def test_crear_app_desde_entorno_con_database_url_vacia_falla():
    with pytest.raises(ConfiguracionInvalida, match="DATABASE_URL"):
        crear_app_desde_entorno({"DATABASE_URL": ""})
