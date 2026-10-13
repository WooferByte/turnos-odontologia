"""Configuración tomada del entorno (design I11). Python no lee archivos .env."""
import os
from collections.abc import Mapping

VARIABLE_DATABASE_URL = "DATABASE_URL"


class ConfiguracionInvalida(Exception):
    """Falta una variable de entorno obligatoria o está vacía."""


def leer_database_url(entorno: Mapping[str, str] = os.environ) -> str:
    """Devuelve ``DATABASE_URL``; no cae en silencio a otra base."""
    url = entorno.get(VARIABLE_DATABASE_URL, "")
    if not url:
        raise ConfiguracionInvalida(
            f"Falta la variable de entorno {VARIABLE_DATABASE_URL} o está vacía"
        )
    return url
