"""Configuración tomada del entorno (design I11, J10). Python no lee archivos .env."""
import os
import secrets
from collections.abc import Mapping
from dataclasses import dataclass, field

from app.domain.acceso.usuarios import MAXIMO_DE_BYTES_DE_CONTRASENA, MINIMO_DE_CARACTERES_DE_CONTRASENA

VARIABLE_DATABASE_URL = "DATABASE_URL"
VARIABLE_JWT_SECRET = "JWT_SECRET"
VARIABLE_SEED_USUARIO_PASSWORD = "SEED_USUARIO_PASSWORD"
VARIABLE_JWT_ACCESS_MINUTES = "JWT_ACCESS_MINUTES"
VARIABLE_JWT_REFRESH_DAYS = "JWT_REFRESH_DAYS"

MINIMO_DE_BYTES_DEL_SECRETO = 32  # D198: clave de 256 bits para HS256 (RFC 7518 §3.2)
MINUTOS_ACCESS_POR_DEFECTO = 15
DIAS_REFRESH_POR_DEFECTO = 7
RONDAS_BCRYPT = 12  # el valor por defecto de bcrypt; no es variable de entorno (J10)


class ConfiguracionInvalida(Exception):
    """Falta una variable de entorno obligatoria o está vacía o es inválida."""


@dataclass(frozen=True)
class ConfiguracionDeSesion:
    secreto: str = field(repr=False)  # nunca en el repr: va a parar a logs y a trazas
    minutos_access: int = MINUTOS_ACCESS_POR_DEFECTO
    dias_refresh: int = DIAS_REFRESH_POR_DEFECTO
    rondas_bcrypt: int = RONDAS_BCRYPT


def leer_database_url(entorno: Mapping[str, str] = os.environ) -> str:
    """Devuelve ``DATABASE_URL``; no cae en silencio a otra base."""
    url = entorno.get(VARIABLE_DATABASE_URL, "")
    if not url:
        raise ConfiguracionInvalida(
            f"Falta la variable de entorno {VARIABLE_DATABASE_URL} o está vacía"
        )
    return url


def _entero_positivo(entorno: Mapping[str, str], variable: str, por_defecto: int) -> int:
    if variable not in entorno:
        return por_defecto
    try:
        valor = int(entorno[variable])
    except ValueError:
        valor = 0
    if valor <= 0:
        raise ConfiguracionInvalida(f"La variable de entorno {variable} debe ser un entero mayor que 0")
    return valor


def leer_configuracion_de_sesion(entorno: Mapping[str, str] = os.environ) -> ConfiguracionDeSesion:
    """Lee ``JWT_*``; los errores nombran la variable y nunca su valor (design J10)."""
    secreto = entorno.get(VARIABLE_JWT_SECRET, "")
    if not secreto:
        raise ConfiguracionInvalida(
            f"Falta la variable de entorno {VARIABLE_JWT_SECRET} o está vacía"
        )
    if len(secreto.encode("utf-8")) < MINIMO_DE_BYTES_DEL_SECRETO:
        raise ConfiguracionInvalida(
            f"La variable de entorno {VARIABLE_JWT_SECRET} debe tener {MINIMO_DE_BYTES_DEL_SECRETO} bytes como mínimo"
        )
    return ConfiguracionDeSesion(
        secreto=secreto,
        minutos_access=_entero_positivo(entorno, VARIABLE_JWT_ACCESS_MINUTES, MINUTOS_ACCESS_POR_DEFECTO),
        dias_refresh=_entero_positivo(entorno, VARIABLE_JWT_REFRESH_DAYS, DIAS_REFRESH_POR_DEFECTO),
    )


def leer_contrasena_del_seed(entorno: Mapping[str, str] = os.environ) -> str:
    """Lee ``SEED_USUARIO_PASSWORD``: de 10 caracteres a 72 bytes (RN-AU-07); el error no muestra el valor."""
    contrasena = entorno.get(VARIABLE_SEED_USUARIO_PASSWORD, "")
    if not contrasena:
        raise ConfiguracionInvalida(
            f"Falta la variable de entorno {VARIABLE_SEED_USUARIO_PASSWORD} o está vacía"
        )
    if len(contrasena) < MINIMO_DE_CARACTERES_DE_CONTRASENA or len(contrasena.encode("utf-8")) > MAXIMO_DE_BYTES_DE_CONTRASENA:
        raise ConfiguracionInvalida(
            f"La variable de entorno {VARIABLE_SEED_USUARIO_PASSWORD} debe tener entre "
            f"{MINIMO_DE_CARACTERES_DE_CONTRASENA} caracteres y {MAXIMO_DE_BYTES_DE_CONTRASENA} bytes"
        )
    return contrasena


def secreto_efimero() -> str:
    """Secreto aleatorio de 64 caracteres para la demo y los tests; muere con el proceso (D196)."""
    return secrets.token_urlsafe(48)
