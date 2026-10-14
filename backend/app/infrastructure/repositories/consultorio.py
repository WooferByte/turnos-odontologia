"""Consulta del consultorio compartida por los repositorios de catálogo (D173, design S9)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.modelos import ConsultorioModelo


def consultorio_unico(sesion: Session) -> int:
    """El id del único consultorio de la instalación; si no hay uno solo, falla."""
    return sesion.scalars(select(ConsultorioModelo.id)).one()
