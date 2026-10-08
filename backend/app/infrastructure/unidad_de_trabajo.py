"""Unidad de trabajo: una sesión por uso; confirma al salir sin error y deshace si hubo uno (D12)."""
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.repositories.agenda import RepositorioAgendaSqlAlchemy


class UnidadDeTrabajoSqlAlchemy:
    def __init__(self, fabrica_sesiones: sessionmaker[Session]) -> None:
        self._fabrica_sesiones = fabrica_sesiones
        self._sesion: Session | None = None
        self.agenda: RepositorioAgendaSqlAlchemy

    def __enter__(self) -> "UnidadDeTrabajoSqlAlchemy":
        self._sesion = self._fabrica_sesiones()
        self.agenda = RepositorioAgendaSqlAlchemy(self._sesion)
        return self

    def __exit__(self, tipo, valor, traza) -> None:
        sesion = self._sesion
        try:
            if tipo is None:
                sesion.commit()
            else:
                sesion.rollback()
        finally:
            sesion.close()
            self._sesion = None
