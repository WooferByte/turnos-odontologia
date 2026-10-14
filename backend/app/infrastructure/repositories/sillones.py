"""Repositorio de sillones sobre SQLAlchemy. Traduce modelos ORM a tipos de dominio (design S9)."""
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.agenda.sillones import DatosSillon
from app.infrastructure.db.modelos import ConsultorioModelo, SillonModelo


def _a_dominio(modelo: SillonModelo) -> DatosSillon:
    return DatosSillon(
        id=modelo.id,
        consultorio_id=modelo.consultorio_id,
        nombre=modelo.nombre,
        activo=modelo.activo,
    )


class RepositorioSillonesSqlAlchemy:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def consultorio_unico(self) -> int:
        return self._sesion.scalars(select(ConsultorioModelo.id)).one()

    def del_consultorio(self, consultorio_id: int) -> Sequence[DatosSillon]:
        consulta = (
            select(SillonModelo)
            .where(SillonModelo.consultorio_id == consultorio_id)
            .order_by(SillonModelo.id)
        )
        return [_a_dominio(m) for m in self._sesion.scalars(consulta)]

    def obtener(self, sillon_id: int) -> DatosSillon | None:
        modelo = self._sesion.get(SillonModelo, sillon_id)
        return None if modelo is None else _a_dominio(modelo)

    def agregar(self, datos: DatosSillon) -> DatosSillon:
        modelo = SillonModelo(
            consultorio_id=datos.consultorio_id, nombre=datos.nombre, activo=datos.activo
        )
        self._sesion.add(modelo)
        self._sesion.flush()  # asigna el id sin confirmar; el commit es de la unidad de trabajo
        return _a_dominio(modelo)

    def guardar(self, datos: DatosSillon) -> DatosSillon:
        modelo = self._sesion.get_one(SillonModelo, datos.id)
        modelo.nombre = datos.nombre
        modelo.activo = datos.activo
        self._sesion.flush()
        return _a_dominio(modelo)
