"""Fábricas de datos de prueba: el horario por defecto del profesional (D263, design H13)."""
from datetime import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.modelos import FranjaHorariaModelo
from tests.factories import franja, un_consultorio, un_profesional


def _franjas(sesion: Session, profesional_id: int) -> list[tuple[int, time, time]]:
    consulta = (
        select(FranjaHorariaModelo.dia_semana, FranjaHorariaModelo.hora_inicio, FranjaHorariaModelo.hora_fin)
        .where(FranjaHorariaModelo.profesional_id == profesional_id)
        .order_by(FranjaHorariaModelo.dia_semana, FranjaHorariaModelo.hora_inicio)
    )
    return [tuple(fila) for fila in sesion.execute(consulta)]


def test_un_profesional_tiene_por_defecto_franjas_0000_2359_de_lunes_a_domingo(sesion: Session) -> None:
    profesional = un_profesional(sesion, un_consultorio(sesion))

    assert _franjas(sesion, profesional.id) == [(dia, time(0, 0), time(23, 59)) for dia in range(7)]


def test_horario_vacio_deja_al_profesional_sin_franjas(sesion: Session) -> None:
    profesional = un_profesional(sesion, un_consultorio(sesion), horario=())

    assert _franjas(sesion, profesional.id) == []


def test_un_horario_explicito_reemplaza_al_de_prueba(sesion: Session) -> None:
    profesional = un_profesional(
        sesion, un_consultorio(sesion), horario=(franja(0, "09:00", "13:00"), franja(0, "15:00", "19:00"))
    )

    assert _franjas(sesion, profesional.id) == [
        (0, time(9, 0), time(13, 0)),
        (0, time(15, 0), time(19, 0)),
    ]
