"""El seed de la demo se puede repetir sin duplicar datos (design I13; RN-PR-01).

Sin dobles: sesión y base SQLite en memoria reales del ``conftest.py``.
"""
from datetime import time

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.domain.acceso.roles import Rol
from app.infrastructure.db.modelos import (
    ConsultorioModelo,
    FranjaHorariaModelo,
    PacienteModelo,
    PrestacionModelo,
    ProfesionalModelo,
    SillonModelo,
    UsuarioModelo,
)
from app.infrastructure.db.seed_demo import (
    CONTRASENA_DEMO,
    EMAIL_RECEPCION_DEMO,
    cargar_demo_si_falta,
    cargar_horario_demo_si_falta,
    cargar_recepcionista_demo_si_falta,
    cargar_roles_demo_si_faltan,
    cargar_usuario_demo,
    cargar_usuario_demo_si_falta,
)
from app.infrastructure.repositories.usuarios import RepositorioUsuariosSqlAlchemy
from app.infrastructure.seguridad.contrasenas import HasherBcrypt

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


def test_us090_ca4_usuario_de_la_demo_con_hash_bcrypt(sesion: Session):
    hasher = HasherBcrypt(4)
    cargar_demo_si_falta(sesion)

    cargar_usuario_demo(sesion, hasher.hashear(CONTRASENA_DEMO))

    usuario = sesion.scalars(select(UsuarioModelo)).one()
    assert usuario.id == 1
    assert usuario.consultorio_id == 1
    assert usuario.email == "odontologa@consultorio-demo.test"
    assert usuario.activo is True
    assert usuario.token_version == 0
    assert usuario.hash_password != CONTRASENA_DEMO
    assert hasher.verificar(CONTRASENA_DEMO, usuario.hash_password) is True
    assert hasher.verificar("otra-contrasena-ficticia", usuario.hash_password) is False


def test_cargar_usuario_demo_si_falta_no_duplica(sesion: Session):
    hash_password = HasherBcrypt(4).hashear(CONTRASENA_DEMO)
    cargar_demo_si_falta(sesion)

    primera = cargar_usuario_demo_si_falta(sesion, hash_password)
    segunda = cargar_usuario_demo_si_falta(sesion, hash_password)

    assert primera is True
    assert segunda is False
    assert sesion.scalar(select(func.count()).select_from(UsuarioModelo)) == 1


def test_cargar_usuario_demo_si_falta_con_el_consultorio_ya_sembrado_y_sin_usuario(
    sesion: Session,
):
    # Volumen sembrado antes de C-06: el consultorio existe y el usuario no (design J11).
    cargar_demo_si_falta(sesion)
    assert sesion.scalar(select(func.count()).select_from(UsuarioModelo)) == 0

    cargado = cargar_usuario_demo_si_falta(sesion, HasherBcrypt(4).hashear(CONTRASENA_DEMO))

    assert cargado is True
    assert _filas(sesion) == [1, 1, 1, 5, 3]
    assert sesion.scalar(select(func.count()).select_from(UsuarioModelo)) == 1


def _sembrar_como_en_c06(sesion: Session) -> None:
    """El estado que dejó C-06: consultorio y usuario 1 sin roles ni vínculo."""
    cargar_demo_si_falta(sesion)
    cargar_usuario_demo(sesion, HasherBcrypt(4).hashear(CONTRASENA_DEMO))


def test_us091_ca4_usuario_del_seed_con_sus_roles_y_su_profesional(sesion: Session):
    _sembrar_como_en_c06(sesion)

    cargado = cargar_roles_demo_si_faltan(sesion)

    assert cargado is True
    assert RepositorioUsuariosSqlAlchemy(sesion).roles_de(1) == frozenset({Rol.ODONTOLOGO, Rol.DUENO})
    assert sesion.get(ProfesionalModelo, 1).usuario_id == 1


def test_cargar_roles_demo_si_faltan_no_duplica(sesion: Session):
    _sembrar_como_en_c06(sesion)  # el usuario sembrado sin roles, como en C-06

    primera = cargar_roles_demo_si_faltan(sesion)
    segunda = cargar_roles_demo_si_faltan(sesion)

    assert (primera, segunda) == (True, False)
    assert RepositorioUsuariosSqlAlchemy(sesion).roles_de(1) == frozenset({Rol.ODONTOLOGO, Rol.DUENO})
    assert sesion.get(ProfesionalModelo, 1).usuario_id == 1


def test_cargar_roles_demo_si_faltan_completa_lo_que_falta_sin_tocar_lo_que_hay(sesion: Session):
    _sembrar_como_en_c06(sesion)
    RepositorioUsuariosSqlAlchemy(sesion).asignar_rol(1, Rol.DUENO)
    sesion.commit()

    cargado = cargar_roles_demo_si_faltan(sesion)

    assert cargado is True
    assert RepositorioUsuariosSqlAlchemy(sesion).roles_de(1) == frozenset({Rol.ODONTOLOGO, Rol.DUENO})


def test_us091_ca3_recepcionista_de_la_demo(sesion: Session):
    hasher = HasherBcrypt(4)
    _sembrar_como_en_c06(sesion)

    primera = cargar_recepcionista_demo_si_falta(sesion, hasher.hashear(CONTRASENA_DEMO))
    segunda = cargar_recepcionista_demo_si_falta(sesion, hasher.hashear(CONTRASENA_DEMO))

    recepcionista = sesion.get(UsuarioModelo, 2)
    assert (primera, segunda) == (True, False)
    assert recepcionista.email == EMAIL_RECEPCION_DEMO == "recepcion@consultorio-demo.test"
    assert recepcionista.activo is True
    assert recepcionista.consultorio_id == 1
    assert hasher.verificar(CONTRASENA_DEMO, recepcionista.hash_password) is True
    assert RepositorioUsuariosSqlAlchemy(sesion).roles_de(2) == frozenset({Rol.RECEPCIONISTA})
    assert sesion.scalar(select(func.count()).select_from(UsuarioModelo)) == 2


# --- US-002 CA-1: el horario de ejemplo de la demo (D56, design H12) --------------------------------
HORARIO_DE_LA_DEMO = [
    (dia, time(desde), time(hasta)) for dia in range(5) for desde, hasta in ((9, 13), (15, 19))
]


def _franjas_del_profesional_1(sesion: Session) -> list[tuple[int, time, time]]:
    consulta = (
        select(FranjaHorariaModelo.dia_semana, FranjaHorariaModelo.hora_inicio, FranjaHorariaModelo.hora_fin)
        .where(FranjaHorariaModelo.profesional_id == 1)
        .order_by(FranjaHorariaModelo.dia_semana, FranjaHorariaModelo.hora_inicio)
    )
    return [tuple(fila) for fila in sesion.execute(consulta)]


def test_us002_ca1_la_demo_arranca_con_el_horario_de_ejemplo(sesion: Session):
    cargar_demo_si_falta(sesion)

    # Diez franjas: 09-13 y 15-19 de lunes a viernes; sábado y domingo sin atención.
    assert _franjas_del_profesional_1(sesion) == HORARIO_DE_LA_DEMO
    assert len(HORARIO_DE_LA_DEMO) == 10


def test_us002_ca1_cargar_horario_demo_si_falta_completa_un_volumen_sin_franjas_y_no_duplica(sesion: Session):
    # Volumen sembrado antes de C-12: el profesional 1 existe y no tiene franjas.
    cargar_demo_si_falta(sesion)
    sesion.execute(delete(FranjaHorariaModelo))
    sesion.commit()
    assert _franjas_del_profesional_1(sesion) == []

    primera = cargar_horario_demo_si_falta(sesion)
    segunda = cargar_horario_demo_si_falta(sesion)

    assert (primera, segunda) == (True, False)
    assert _franjas_del_profesional_1(sesion) == HORARIO_DE_LA_DEMO


def test_us002_ca1_cargar_horario_demo_si_falta_respeta_el_horario_que_ya_tiene(sesion: Session):
    cargar_demo_si_falta(sesion)
    sesion.execute(delete(FranjaHorariaModelo))
    sesion.add(
        FranjaHorariaModelo(profesional_id=1, dia_semana=6, hora_inicio=time(10, 0), hora_fin=time(12, 0))
    )
    sesion.commit()

    cargado = cargar_horario_demo_si_falta(sesion)

    assert cargado is False
    assert _franjas_del_profesional_1(sesion) == [(6, time(10, 0), time(12, 0))]


def test_us002_ca1_cargar_horario_demo_si_falta_sin_profesional_no_hace_nada(sesion: Session):
    assert cargar_horario_demo_si_falta(sesion) is False
    assert sesion.scalar(select(func.count()).select_from(FranjaHorariaModelo)) == 0
