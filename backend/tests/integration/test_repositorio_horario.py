"""Repositorio del horario sobre SQLite en memoria (US-002 CA-1; HOR-1; design H2, H3)."""
from datetime import date, time

from sqlalchemy.orm import Session

from app.domain.agenda.horario import Franja
from app.domain.agenda.profesionales import DatosProfesional
from app.infrastructure.repositories.horario import RepositorioHorarioSqlAlchemy
from tests.factories import franja, un_consultorio, un_profesional


def test_us002_ca1_reemplazar_guarda_las_franjas_y_franjas_de_las_devuelve_por_dia_y_hora(
    sesion: Session, fabrica_sesiones
) -> None:
    consultorio = un_consultorio(sesion)
    profesional = un_profesional(sesion, consultorio, horario=())

    with fabrica_sesiones() as escritura:
        RepositorioHorarioSqlAlchemy(escritura).reemplazar(
            profesional.id,
            [franja(2, "15:00", "19:00"), franja(0, "09:00", "13:00"), franja(2, "09:00", "13:00")],
        )
        escritura.commit()

    with fabrica_sesiones() as lectura:
        leidas = RepositorioHorarioSqlAlchemy(lectura).franjas_de(profesional.id)
    assert leidas == [
        Franja(0, time(9, 0), time(13, 0)),
        Franja(2, time(9, 0), time(13, 0)),
        Franja(2, time(15, 0), time(19, 0)),
    ]


def test_us002_ca1_reemplazar_quita_las_anteriores_y_guarda_la_vigencia_si_la_hay(
    sesion: Session, fabrica_sesiones
) -> None:
    consultorio = un_consultorio(sesion)
    profesional = un_profesional(sesion, consultorio, horario=(franja(1, "10:00", "11:00"),))

    with fabrica_sesiones() as escritura:
        RepositorioHorarioSqlAlchemy(escritura).reemplazar(
            profesional.id, [franja(4, "08:00", "12:00", date(2026, 1, 1), date(2026, 12, 31))]
        )
        escritura.commit()

    with fabrica_sesiones() as lectura:
        leidas = RepositorioHorarioSqlAlchemy(lectura).franjas_de(profesional.id)
    assert leidas == [Franja(4, time(8, 0), time(12, 0), date(2026, 1, 1), date(2026, 12, 31))]


def test_us002_ca1_reemplazar_con_la_lista_vacia_deja_al_profesional_sin_franjas(
    sesion: Session, fabrica_sesiones
) -> None:
    consultorio = un_consultorio(sesion)
    profesional = un_profesional(sesion, consultorio, horario=(franja(0, "09:00", "13:00"),))

    with fabrica_sesiones() as escritura:
        RepositorioHorarioSqlAlchemy(escritura).reemplazar(profesional.id, [])
        escritura.commit()

    with fabrica_sesiones() as lectura:
        assert RepositorioHorarioSqlAlchemy(lectura).franjas_de(profesional.id) == []


def test_us002_ca1_reemplazar_solo_toca_al_profesional_indicado(sesion: Session, fabrica_sesiones) -> None:
    consultorio = un_consultorio(sesion)
    uno = un_profesional(sesion, consultorio, horario=(franja(0, "09:00", "13:00"),))
    otro = un_profesional(sesion, consultorio, horario=(franja(3, "14:00", "18:00"),))

    with fabrica_sesiones() as escritura:
        RepositorioHorarioSqlAlchemy(escritura).reemplazar(uno.id, [])
        escritura.commit()

    with fabrica_sesiones() as lectura:
        assert RepositorioHorarioSqlAlchemy(lectura).franjas_de(otro.id) == [
            Franja(3, time(14, 0), time(18, 0))
        ]


def test_us002_ca1_profesionales_del_consultorio_devuelve_activos_e_inactivos_por_id_y_no_los_de_otro(
    sesion: Session,
) -> None:
    uno = un_consultorio(sesion)
    otro = un_consultorio(sesion)
    primero = un_profesional(sesion, uno, nombre="Dra. Ficticia A")
    segundo = un_profesional(sesion, uno, nombre="Dr. Ficticio B", activo=False)
    un_profesional(sesion, otro, nombre="Dra. Ajena")

    traidos = RepositorioHorarioSqlAlchemy(sesion).profesionales_del_consultorio(uno.id)

    assert traidos == [
        DatosProfesional(primero.id, uno.id, "Dra. Ficticia A", True),
        DatosProfesional(segundo.id, uno.id, "Dr. Ficticio B", False),
    ]


def test_us002_ca1_profesional_devuelve_el_registro_o_none(sesion: Session) -> None:
    consultorio = un_consultorio(sesion)
    profesional = un_profesional(sesion, consultorio, nombre="Dra. Ficticia", activo=False)
    repositorio = RepositorioHorarioSqlAlchemy(sesion)

    assert repositorio.profesional(profesional.id) == DatosProfesional(
        profesional.id, consultorio.id, "Dra. Ficticia", False
    )
    assert repositorio.profesional(999) is None
