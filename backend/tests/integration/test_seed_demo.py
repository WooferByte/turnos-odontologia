"""El seed de la demo se puede repetir sin duplicar datos (design I13; RN-PR-01).

Sin dobles: sesión y base SQLite en memoria reales del ``conftest.py``.
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.db.modelos import (
    ConsultorioModelo,
    PacienteModelo,
    PrestacionModelo,
    ProfesionalModelo,
    SillonModelo,
)
from app.infrastructure.db.seed_demo import cargar_demo_si_falta

_TABLAS_SEMBRADAS = (
    ConsultorioModelo,
    ProfesionalModelo,
    SillonModelo,
    PrestacionModelo,
    PacienteModelo,
)


def _filas(sesion: Session) -> list[int]:
    return [sesion.scalar(select(func.count()).select_from(tabla)) for tabla in _TABLAS_SEMBRADAS]


def test_cargar_demo_si_falta_no_duplica(sesion: Session):
    primera = cargar_demo_si_falta(sesion)
    filas_tras_la_primera = _filas(sesion)
    segunda = cargar_demo_si_falta(sesion)

    assert primera is True
    assert segunda is False
    assert filas_tras_la_primera == [1, 1, 1, 5, 3]
    assert _filas(sesion) == filas_tras_la_primera
