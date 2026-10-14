"""Repositorio de prestaciones sobre SQLAlchemy. Traduce modelos ORM a tipos de dominio (design P11)."""
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.puertos import NombreRepetidoEnLaBase
from app.domain.agenda.prestaciones import DatosPrestacion
from app.infrastructure.db.modelos import ConsultorioModelo, PrestacionModelo

SQLSTATE_UNICIDAD = "23505"  # unique_violation
RESTRICCION_DE_NOMBRE = "uq_prestacion_consultorio_id_nombre"
MENSAJE_DE_NOMBRE_EN_SQLITE = "UNIQUE constraint failed: prestacion.consultorio_id, prestacion.nombre"


def _a_dominio(modelo: PrestacionModelo) -> DatosPrestacion:
    return DatosPrestacion(
        id=modelo.id,
        consultorio_id=modelo.consultorio_id,
        nombre=modelo.nombre,
        duracion_minutos=modelo.duracion_minutos,
        color=modelo.color,
        reservable_online=modelo.reservable_online,
        activa=modelo.activa,
    )


def _es_nombre_repetido(error: IntegrityError) -> bool:
    """Solo la restricción del nombre; cualquier otra violación sube tal cual (design V3)."""
    if getattr(error.orig, "sqlstate", None) == SQLSTATE_UNICIDAD:
        restriccion = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        return restriccion == RESTRICCION_DE_NOMBRE
    return MENSAJE_DE_NOMBRE_EN_SQLITE in str(error.orig)


class RepositorioPrestacionesSqlAlchemy:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def consultorio_unico(self) -> int:
        return self._sesion.scalars(select(ConsultorioModelo.id)).one()

    def del_consultorio(self, consultorio_id: int) -> Sequence[DatosPrestacion]:
        consulta = (
            select(PrestacionModelo)
            .where(PrestacionModelo.consultorio_id == consultorio_id)
            .order_by(PrestacionModelo.id)
        )
        return [_a_dominio(m) for m in self._sesion.scalars(consulta)]

    def obtener(self, prestacion_id: int) -> DatosPrestacion | None:
        modelo = self._sesion.get(PrestacionModelo, prestacion_id)
        return None if modelo is None else _a_dominio(modelo)

    def agregar(self, datos: DatosPrestacion) -> DatosPrestacion:
        modelo = PrestacionModelo(
            consultorio_id=datos.consultorio_id,
            nombre=datos.nombre,
            duracion_minutos=datos.duracion_minutos,
            color=datos.color,
            reservable_online=datos.reservable_online,
            activa=datos.activa,
        )
        self._sesion.add(modelo)
        self._enviar_a_la_base()
        return _a_dominio(modelo)

    def guardar(self, datos: DatosPrestacion) -> DatosPrestacion:
        modelo = self._sesion.get_one(PrestacionModelo, datos.id)
        modelo.nombre = datos.nombre
        modelo.duracion_minutos = datos.duracion_minutos
        modelo.color = datos.color
        modelo.reservable_online = datos.reservable_online
        modelo.activa = datos.activa
        self._enviar_a_la_base()
        return _a_dominio(modelo)

    def _enviar_a_la_base(self) -> None:
        try:
            self._sesion.flush()  # asigna el id sin confirmar; el commit es de la unidad de trabajo
        except IntegrityError as error:
            if _es_nombre_repetido(error):
                raise NombreRepetidoEnLaBase() from error
            raise
