"""El dominio solo importa la biblioteca estándar y a sí mismo (D70, D132, regla dura 3)."""
import ast
import sys
from pathlib import Path

import pytest

RAIZ_DOMINIO = Path(__file__).resolve().parents[2] / "app" / "domain"


def _es_dominio(modulo: str) -> bool:
    return modulo == "app.domain" or modulo.startswith("app.domain.")


def imports_prohibidos(codigo_fuente: str) -> list[str]:
    """Nombres de los módulos importados que el dominio no puede usar."""
    prohibidos: list[str] = []
    for nodo in ast.walk(ast.parse(codigo_fuente)):
        if isinstance(nodo, ast.Import):
            modulos = [alias.name for alias in nodo.names]
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level > 0:  # import relativo: queda dentro del paquete
                continue
            modulos = [nodo.module or ""]
        else:
            continue
        for modulo in modulos:
            if modulo.split(".")[0] in sys.stdlib_module_names or _es_dominio(modulo):
                continue
            prohibidos.append(modulo)
    return prohibidos


def test_el_dominio_no_importa_nada_fuera_de_la_biblioteca_estandar():
    archivos = sorted(RAIZ_DOMINIO.rglob("*.py"))
    assert archivos, f"No se encontró ningún .py en {RAIZ_DOMINIO}"

    infractores = {
        str(archivo.relative_to(RAIZ_DOMINIO)): imports_prohibidos(archivo.read_text(encoding="utf-8"))
        for archivo in archivos
    }

    assert {a: m for a, m in infractores.items() if m} == {}


@pytest.mark.parametrize(
    ("codigo", "esperado"),
    [
        ("import sqlalchemy", ["sqlalchemy"]),
        ("from fastapi import FastAPI", ["fastapi"]),
        ("from app.infrastructure.db import modelos", ["app.infrastructure.db"]),
        ("import tzdata", ["tzdata"]),
        ("import pydantic, os", ["pydantic"]),
    ],
)
def test_la_funcion_detecta_imports_prohibidos(codigo, esperado):
    assert imports_prohibidos(codigo) == esperado


@pytest.mark.parametrize(
    "codigo",
    [
        "from zoneinfo import ZoneInfo",
        "from app.domain.tiempo import utc_now",
        "import dataclasses",
        "from . import errors",
        "from .errors import FechaNoUTC",
    ],
)
def test_la_funcion_acepta_imports_permitidos(codigo):
    assert imports_prohibidos(codigo) == []
