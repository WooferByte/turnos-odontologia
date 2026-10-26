"""Repositorio de bloqueos sobre SQLAlchemy. Traduce modelos ORM a tipos de dominio (design B2)."""
from collections.abc import Sequence

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.orm import Session

from app.domain.agenda.bloqueos import DatosBloqueo
from app.domain.agenda.intervalo import Intervalo
from app.infrastructure.db.modelos import BloqueoModelo


def _a_dominio(modelo: BloqueoModelo) -> DatosBloqueo:
    return DatosBloqueo(
        id=modelo.id,
        consultorio_id=modelo.consultorio_id,
        profesional_id=modelo.profesional_id,
        sillon_id=modelo.sillon_id,
        inicio=modelo.inicio,
        fin=modelo.fin,
        motivo=modelo.motivo,
        creado_por=modelo.creado_por,
    )


class RepositorioBloqueosSqlAlchemy:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def agregar(self, datos: DatosBloqueo) -> DatosBloqueo:
        modelo = BloqueoModelo(
            consultorio_id=datos.consultorio_id,
            profesional_id=datos.profesional_id,
            sillon_id=datos.sillon_id,
            inicio=datos.inicio,
            fin=datos.fin,
            motivo=datos.motivo,
            creado_por=datos.creado_por,
        )
        self._sesion.add(modelo)
        self._sesion.flush()  # asigna el id sin confirmar; el commit es de la unidad de trabajo
        return _a_dominio(modelo)

    def del_consultorio(self, consultorio_id: int) -> Sequence[DatosBloqueo]:
        consulta = (
            select(BloqueoModelo)
            .where(BloqueoModelo.consultorio_id == consultorio_id)
            .order_by(BloqueoModelo.inicio, BloqueoModelo.id)
        )
        return [_a_dominio(m) for m in self._sesion.scalars(consulta)]

    def obtener(self, bloqueo_id: int) -> DatosBloqueo | None:
        modelo = self._sesion.get(BloqueoModelo, bloqueo_id)
        return None if modelo is None else _a_dominio(modelo)

    def eliminar(self, bloqueo_id: int) -> None:
        self._sesion.execute(delete(BloqueoModelo).where(BloqueoModelo.id == bloqueo_id))
        self._sesion.flush()

    def que_intersecan(
        self, consultorio_id: int, profesional_id: int, sillon_id: int, intervalo: Intervalo
    ) -> Sequence[DatosBloqueo]:
        # Recorte por rango y por alcance; qué bloqueo informar lo decide el dominio (B10).
        consulta = select(BloqueoModelo).where(
            BloqueoModelo.consultorio_id == consultorio_id,
            BloqueoModelo.inicio < intervalo.fin,
            BloqueoModelo.fin > intervalo.inicio,
            or_(
                BloqueoModelo.profesional_id == profesional_id,
                BloqueoModelo.sillon_id == sillon_id,
                and_(BloqueoModelo.profesional_id.is_(None), BloqueoModelo.sillon_id.is_(None)),
            ),
        )
        return [_a_dominio(m) for m in self._sesion.scalars(consulta)]
