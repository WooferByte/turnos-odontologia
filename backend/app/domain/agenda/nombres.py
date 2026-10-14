"""Nombres de los catálogos: normalización y clave de comparación. Solo biblioteca estándar."""
import unicodedata


def normalizar_espacios(nombre: str) -> str:
    """Quita los espacios de los extremos y colapsa los internos; es lo que se guarda."""
    return " ".join(nombre.split())


def clave_de_nombre(nombre: str) -> str:
    """Clave para comparar nombres sin mayúsculas, acentos ni espacios de más; nunca se guarda."""
    descompuesto = unicodedata.normalize("NFKD", normalizar_espacios(nombre).casefold())
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")
