"""Guard de fechas (DD-13, D15): ninguna columna ni llamada puede producir fechas naive.

No usa base, pero importa los modelos de SQLAlchemy; por eso vive en ``integration``.
"""
import ast
from pathlib import Path

import pytest
from sqlalchemy import Column, DateTime, Integer, MetaData, Table
from sqlalchemy.types import TypeDecorator

from app.infrastructure.db.modelos import Base
from app.infrastructure.db.tipos import FechaHoraUTC

RAIZ_APP = Path(__file__).resolve().parents[2] / "app"
LLAMADAS_SIEMPRE_PROHIBIDAS = {"utcnow", "utcfromtimestamp", "today"}


def _es_columna_de_fecha(tipo) -> bool:
    if isinstance(tipo, TypeDecorator):
        return isinstance(tipo.impl, DateTime)
    return isinstance(tipo, DateTime)


def columnas_de_fecha_mal_tipadas(metadata: MetaData) -> tuple[list[str], int]:
    """Devuelve (columnas de fecha que no son ``FechaHoraUTC`` con zona, total de columnas de fecha)."""
    mal_tipadas: list[str] = []
    total = 0
    for tabla in metadata.tables.values():
        for columna in tabla.columns:
            if not _es_columna_de_fecha(columna.type):
                continue
            total += 1
            bien = isinstance(columna.type, FechaHoraUTC) and columna.type.impl.timezone
            if not bien:
                mal_tipadas.append(f"{tabla.name}.{columna.name}")
    return mal_tipadas, total


def llamadas_a_fechas_prohibidas(codigo_fuente: str, permitir_now: bool = False) -> list[str]:
    """Llamadas ``.utcnow()``, ``.utcfromtimestamp()``, ``.today()`` y, salvo que se permita, ``.now(...)``."""
    prohibidas = set(LLAMADAS_SIEMPRE_PROHIBIDAS)
    if not permitir_now:
        prohibidas.add("now")
    encontradas = []
    for nodo in ast.walk(ast.parse(codigo_fuente)):
        if (
            isinstance(nodo, ast.Call)
            and isinstance(nodo.func, ast.Attribute)
            and nodo.func.attr in prohibidas
        ):
            encontradas.append(nodo.func.attr)
    return encontradas


# --- Parte 1: esquema ---
def test_toda_columna_de_fecha_hora_es_fecha_hora_utc_con_zona():
    mal_tipadas, total = columnas_de_fecha_mal_tipadas(Base.metadata)

    assert total >= 3, "No se encontraron las columnas de fecha-hora de turno"
    assert mal_tipadas == []


def test_la_funcion_de_esquema_detecta_una_columna_con_datetime_sin_zona():
    metadata = MetaData()
    Table("ejemplo", metadata, Column("id", Integer, primary_key=True), Column("cuando", DateTime()))
    Table("ejemplo_zona", metadata, Column("cuando", DateTime(timezone=True)))

    mal_tipadas, total = columnas_de_fecha_mal_tipadas(metadata)

    assert mal_tipadas == ["ejemplo.cuando", "ejemplo_zona.cuando"]
    assert total == 2


# --- Parte 2: código ---
def test_el_codigo_de_la_aplicacion_no_crea_fechas_naive():
    archivos = sorted(RAIZ_APP.rglob("*.py"))
    assert archivos, f"No se encontró ningún .py en {RAIZ_APP}"
    reloj = RAIZ_APP / "domain" / "tiempo.py"

    infractores = {}
    for archivo in archivos:
        encontradas = llamadas_a_fechas_prohibidas(
            archivo.read_text(encoding="utf-8"), permitir_now=archivo == reloj
        )
        if encontradas:
            infractores[str(archivo.relative_to(RAIZ_APP))] = encontradas

    assert infractores == {}


@pytest.mark.parametrize(
    ("codigo", "permitir_now", "esperado"),
    [
        ("import datetime\nx = datetime.datetime.utcnow()", False, ["utcnow"]),
        ("from datetime import datetime\nx = datetime.utcfromtimestamp(0)", False, ["utcfromtimestamp"]),
        ("from datetime import date\nx = date.today()", False, ["today"]),
        ("from datetime import datetime\nx = datetime.now()", False, ["now"]),
        ("from datetime import datetime\nx = datetime.now(UTC)", False, ["now"]),
        ("from datetime import datetime\nx = datetime.utcnow()", True, ["utcnow"]),
        ("from datetime import datetime\nx = datetime.now(UTC)", True, []),
        ("x = reloj()", False, []),
    ],
)
def test_la_funcion_de_codigo_detecta_llamadas_prohibidas(codigo, permitir_now, esperado):
    assert llamadas_a_fechas_prohibidas(codigo, permitir_now) == esperado
