"""Repositorio de bloqueos y lectura de turnos afectados sobre SQLite en memoria (US-003; E10; design B2, B3, B9)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.agenda.bloqueos import Alcance, DatosBloqueo
from app.domain.agenda.intervalo import Intervalo
from app.infrastructure.db.modelos import TurnoModelo
from app.infrastructure.repositories.agenda import RepositorioAgendaSqlAlchemy
from app.infrastructure.repositories.bloqueos import RepositorioBloqueosSqlAlchemy
from tests.conftest import a_las
from tests.factories import (
    un_bloqueo,
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
    un_usuario,
)


def _datos(consultorio_id: int, creado_por: int, desde, hasta, **ids) -> DatosBloqueo:
    return DatosBloqueo(
        id=None,
        consultorio_id=consultorio_id,
        profesional_id=ids.get("profesional_id"),
        sillon_id=ids.get("sillon_id"),
        inicio=desde,
        fin=hasta,
        motivo="Vacaciones",
        creado_por=creado_por,
    )


def test_us003_ca1_agregar_guarda_el_bloqueo_y_del_consultorio_los_devuelve_por_inicio_e_id_sin_los_de_otro(
    sesion: Session, fabrica_sesiones
) -> None:
    consultorio = un_consultorio(sesion)
    otro = un_consultorio(sesion)
    usuario = un_usuario(sesion, consultorio)
    profesional = un_profesional(sesion, consultorio)
    un_bloqueo(sesion, otro, inicio=a_las(8), fin=a_las(9))

    with fabrica_sesiones() as escritura:
        repositorio = RepositorioBloqueosSqlAlchemy(escritura)
        tarde = repositorio.agregar(_datos(consultorio.id, usuario.id, a_las(14), a_las(15)))
        temprano = repositorio.agregar(
            _datos(consultorio.id, usuario.id, a_las(10), a_las(12), profesional_id=profesional.id)
        )
        igual_hora = repositorio.agregar(_datos(consultorio.id, usuario.id, a_las(10), a_las(11)))
        escritura.commit()

    with fabrica_sesiones() as lectura:
        leidos = RepositorioBloqueosSqlAlchemy(lectura).del_consultorio(consultorio.id)
    assert [b.id for b in leidos] == [temprano.id, igual_hora.id, tarde.id]
    assert leidos[0] == temprano
    assert temprano.id is not None and temprano.alcance is Alcance.PROFESIONAL
    assert (leidos[0].inicio, leidos[0].fin, leidos[0].creado_por) == (a_las(10), a_las(12), usuario.id)
    assert leidos[0].inicio.tzinfo is not None


def test_us003_ca1_obtener_devuelve_el_bloqueo_o_none(sesion: Session) -> None:
    consultorio = un_consultorio(sesion)
    guardado = un_bloqueo(sesion, consultorio, inicio=a_las(10), fin=a_las(11), motivo="Feriado")
    repositorio = RepositorioBloqueosSqlAlchemy(sesion)

    obtenido = repositorio.obtener(guardado.id)

    assert obtenido is not None and (obtenido.id, obtenido.motivo, obtenido.alcance) == (
        guardado.id,
        "Feriado",
        Alcance.CONSULTORIO,
    )
    assert repositorio.obtener(999) is None


def test_us003_ca1_eliminar_quita_el_bloqueo_y_no_toca_turnos(sesion: Session, fabrica_sesiones) -> None:
    consultorio = un_consultorio(sesion)
    profesional = un_profesional(sesion, consultorio)
    sillon = un_sillon(sesion, consultorio)
    turno = un_turno(
        sesion,
        paciente=un_paciente(sesion, consultorio),
        profesional=profesional,
        sillon=sillon,
        prestacion=una_prestacion(sesion, consultorio),
        inicio=a_las(13),
    )
    bloqueo = un_bloqueo(sesion, consultorio, inicio=a_las(12), fin=a_las(16), profesional=profesional)
    otro = un_bloqueo(sesion, consultorio, inicio=a_las(12), fin=a_las(16), sillon=sillon)

    with fabrica_sesiones() as escritura:
        RepositorioBloqueosSqlAlchemy(escritura).eliminar(bloqueo.id)
        escritura.commit()

    with fabrica_sesiones() as lectura:
        assert [b.id for b in RepositorioBloqueosSqlAlchemy(lectura).del_consultorio(consultorio.id)] == [otro.id]
        assert lectura.scalars(select(TurnoModelo.id)).all() == [turno.id]


def test_e10_que_intersecan_devuelve_los_bloqueos_del_profesional_del_sillon_y_del_consultorio_que_intersecan(
    sesion: Session,
) -> None:
    consultorio = un_consultorio(sesion)
    profesional = un_profesional(sesion, consultorio)
    otro_profesional = un_profesional(sesion, consultorio)
    sillon = un_sillon(sesion, consultorio)
    otro_sillon = un_sillon(sesion, consultorio)
    ajeno = un_consultorio(sesion)
    del_profesional = un_bloqueo(sesion, consultorio, inicio=a_las(10), fin=a_las(12), profesional=profesional)
    del_sillon = un_bloqueo(sesion, consultorio, inicio=a_las(11), fin=a_las(13), sillon=sillon)
    del_consultorio = un_bloqueo(sesion, consultorio, inicio=a_las(11, 30), fin=a_las(12, 30))
    un_bloqueo(sesion, consultorio, inicio=a_las(10), fin=a_las(12), profesional=otro_profesional)
    un_bloqueo(sesion, consultorio, inicio=a_las(10), fin=a_las(12), sillon=otro_sillon)
    un_bloqueo(sesion, ajeno, inicio=a_las(10), fin=a_las(12))
    contiguo = un_bloqueo(sesion, consultorio, inicio=a_las(9), fin=a_las(11, 30), profesional=profesional)
    repositorio = RepositorioBloqueosSqlAlchemy(sesion)

    adentro = repositorio.que_intersecan(
        consultorio.id, profesional.id, sillon.id, Intervalo(a_las(11, 30), a_las(12))
    )
    afuera = repositorio.que_intersecan(
        consultorio.id, profesional.id, sillon.id, Intervalo(a_las(13), a_las(14))
    )

    assert sorted(b.id for b in adentro) == sorted([del_profesional.id, del_sillon.id, del_consultorio.id])
    assert contiguo.id not in {b.id for b in adentro}  # termina justo cuando empieza el turno
    assert afuera == []


def test_us003_ca2_turnos_activos_que_intersecan_filtra_por_alcance_estado_e_interseccion(sesion: Session) -> None:
    consultorio = un_consultorio(sesion)
    paciente = un_paciente(sesion, consultorio)
    prestacion = una_prestacion(sesion, consultorio)  # 30 minutos
    profesional = un_profesional(sesion, consultorio)
    otro_profesional = un_profesional(sesion, consultorio)
    sillon = un_sillon(sesion, consultorio)
    otro_sillon = un_sillon(sesion, consultorio)
    ajeno = un_consultorio(sesion)

    def turno(prof, sill, inicio, **kw):
        return un_turno(
            sesion, paciente=paciente, profesional=prof, sillon=sill, prestacion=prestacion, inicio=inicio, **kw
        )

    uno = turno(profesional, sillon, a_las(13))
    del_otro = turno(otro_profesional, otro_sillon, a_las(14))
    turno(profesional, sillon, a_las(13, 30), estado="cancelado_paciente")
    turno(profesional, sillon, a_las(11, 30))  # termina justo cuando empieza el bloqueo
    turno(profesional, sillon, a_las(16))  # empieza justo cuando termina
    un_minuto = turno(profesional, sillon, a_las(15, 59))
    turno_ajeno = un_turno(
        sesion,
        paciente=un_paciente(sesion, ajeno),
        profesional=un_profesional(sesion, ajeno),
        sillon=un_sillon(sesion, ajeno),
        prestacion=una_prestacion(sesion, ajeno),
        inicio=a_las(13),
    )
    repositorio = RepositorioAgendaSqlAlchemy(sesion)

    def ids(**ids_) -> list[int]:
        bloqueo = _datos(consultorio.id, 1, a_las(12), a_las(16), **ids_)
        return sorted(t.id for t in repositorio.turnos_activos_que_intersecan(bloqueo))

    assert ids(profesional_id=profesional.id) == sorted([uno.id, un_minuto.id])
    assert ids(sillon_id=otro_sillon.id) == [del_otro.id]
    assert ids() == sorted([uno.id, un_minuto.id, del_otro.id])
    assert turno_ajeno.id not in ids()
