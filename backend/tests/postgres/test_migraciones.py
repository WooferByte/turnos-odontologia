"""Perfil opcional con PostgreSQL: migraciones y esquema (INF-1, INF-4)."""
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

pytestmark = pytest.mark.postgres


def test_el_perfil_se_conecta_a_postgresql(sesion: Session) -> None:
    assert sesion.execute(text("SELECT 1")).scalar_one() == 1
