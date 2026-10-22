"""Repositorio de usuarios sobre SQLite en memoria (US-090 CA-4 borde; RN-AU-03; design J3, J6)."""
from dataclasses import replace

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.puertos import EmailRepetidoEnLaBase, RolInvalidoEnLaBase
from app.domain.acceso.roles import Rol
from app.domain.acceso.usuarios import DatosUsuario
from app.infrastructure.db.modelos import UsuarioModelo, UsuarioRolModelo
from app.infrastructure.repositories.usuarios import RepositorioUsuariosSqlAlchemy
from tests.conftest import RELOJ_FIJO
from tests.factories import un_consultorio, un_profesional, un_usuario

EMAIL = "odontologa@consultorio-demo.test"


def _nuevo(consultorio_id: int, email: str = EMAIL, **cambios) -> DatosUsuario:
    base = DatosUsuario(
        id=None,
        consultorio_id=consultorio_id,
        email=email,
        hash_password="$2b$04$hash-ficticio-de-prueba",
        activo=True,
        token_version=0,
        creado_en=RELOJ_FIJO,
    )
    return replace(base, **cambios)


def _cantidad_de_usuarios(sesion: Session) -> int:
    return sesion.scalar(select(func.count()).select_from(UsuarioModelo))


def test_us090_ca4_agregar_guarda_el_email_normalizado_y_devuelve_el_usuario_con_id(
    sesion: Session, fabrica_sesiones
) -> None:
    consultorio = un_consultorio(sesion)

    with fabrica_sesiones() as escritura:
        guardado = RepositorioUsuariosSqlAlchemy(escritura).agregar(
            _nuevo(consultorio.id, email=" Odontologa@Consultorio-Demo.TEST ")
        )
        escritura.commit()

    assert guardado.id is not None
    assert guardado.email == EMAIL
    assert sesion.scalar(select(UsuarioModelo.email)) == EMAIL


def test_us090_ca4_otra_sesion_lee_al_usuario_por_email_y_por_id_con_sus_siete_campos(
    sesion: Session, fabrica_sesiones
) -> None:
    consultorio = un_consultorio(sesion)
    with fabrica_sesiones() as escritura:
        guardado = RepositorioUsuariosSqlAlchemy(escritura).agregar(
            _nuevo(consultorio.id, activo=False, token_version=3)
        )
        escritura.commit()
    esperado = DatosUsuario(
        id=guardado.id,
        consultorio_id=consultorio.id,
        email=EMAIL,
        hash_password="$2b$04$hash-ficticio-de-prueba",
        activo=False,
        token_version=3,
        creado_en=RELOJ_FIJO,
    )

    with fabrica_sesiones() as lectura:
        repositorio = RepositorioUsuariosSqlAlchemy(lectura)
        por_email = repositorio.por_email(EMAIL)
        por_id = repositorio.obtener(guardado.id)

    assert por_email == esperado
    assert por_id == esperado
    assert por_id.creado_en.tzinfo is not None  # aware UTC (RN-GL-01)


def test_us090_ca2_por_email_inexistente_y_obtener_inexistente_dan_none(sesion: Session) -> None:
    repositorio = RepositorioUsuariosSqlAlchemy(sesion)

    assert repositorio.por_email("nadie@consultorio-demo.test") is None
    assert repositorio.obtener(999) is None


def test_us090_ca4_email_repetido_sin_distinguir_mayusculas(sesion: Session, fabrica_sesiones) -> None:
    consultorio = un_consultorio(sesion)
    with fabrica_sesiones() as primera:
        RepositorioUsuariosSqlAlchemy(primera).agregar(_nuevo(consultorio.id))
        primera.commit()

    with fabrica_sesiones() as segunda:
        with pytest.raises(EmailRepetidoEnLaBase):
            RepositorioUsuariosSqlAlchemy(segunda).agregar(
                _nuevo(consultorio.id, email=" Odontologa@Consultorio-Demo.TEST ")
            )

    assert _cantidad_de_usuarios(sesion) == 1


def test_us090_ca4_la_unidad_de_trabajo_expone_usuarios_sobre_la_misma_sesion_que_agenda(
    sesion: Session, uow
) -> None:
    consultorio = un_consultorio(sesion)

    with uow:
        agregado = uow.usuarios.agregar(_nuevo(consultorio.id))
        leido = uow.usuarios.obtener(agregado.id)
        zona = uow.agenda.zona_horaria(consultorio.id)

    assert leido == agregado
    assert zona == consultorio.zona_horaria
    assert _cantidad_de_usuarios(sesion) == 1


def test_us091_ca1_roles_de_un_usuario(sesion: Session, fabrica_sesiones) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))
    with fabrica_sesiones() as escritura:
        repositorio = RepositorioUsuariosSqlAlchemy(escritura)
        repositorio.asignar_rol(usuario.id, Rol.ODONTOLOGO)
        repositorio.asignar_rol(usuario.id, Rol.DUENO)
        escritura.commit()

    with fabrica_sesiones() as lectura:
        roles = RepositorioUsuariosSqlAlchemy(lectura).roles_de(usuario.id)

    assert roles == frozenset({Rol.ODONTOLOGO, Rol.DUENO})


def test_us091_ca1_usuario_sin_roles(sesion: Session) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))

    assert RepositorioUsuariosSqlAlchemy(sesion).roles_de(usuario.id) == frozenset()


def test_us091_ca1_los_roles_de_cada_usuario_no_se_mezclan(sesion: Session, fabrica_sesiones) -> None:
    consultorio = un_consultorio(sesion)
    uno, otro = un_usuario(sesion, consultorio), un_usuario(sesion, consultorio)
    with fabrica_sesiones() as escritura:
        RepositorioUsuariosSqlAlchemy(escritura).asignar_rol(uno.id, Rol.RECEPCIONISTA)
        escritura.commit()

    repositorio = RepositorioUsuariosSqlAlchemy(sesion)

    assert repositorio.roles_de(uno.id) == frozenset({Rol.RECEPCIONISTA})
    assert repositorio.roles_de(otro.id) == frozenset()


def test_us091_ca1_rol_repetido_se_rechaza(sesion: Session, fabrica_sesiones) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))
    with fabrica_sesiones() as primera:
        RepositorioUsuariosSqlAlchemy(primera).asignar_rol(usuario.id, Rol.DUENO)
        primera.commit()

    with fabrica_sesiones() as segunda:
        with pytest.raises(RolInvalidoEnLaBase):
            RepositorioUsuariosSqlAlchemy(segunda).asignar_rol(usuario.id, Rol.DUENO)

    assert RepositorioUsuariosSqlAlchemy(sesion).roles_de(usuario.id) == frozenset({Rol.DUENO})


def test_us091_ca5_quitar_rol(sesion: Session, fabrica_sesiones) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))
    with fabrica_sesiones() as escritura:
        repositorio = RepositorioUsuariosSqlAlchemy(escritura)
        repositorio.asignar_rol(usuario.id, Rol.ODONTOLOGO)
        repositorio.asignar_rol(usuario.id, Rol.DUENO)
        escritura.commit()

    with fabrica_sesiones() as quitando:
        RepositorioUsuariosSqlAlchemy(quitando).quitar_rol(usuario.id, Rol.ODONTOLOGO)
        quitando.commit()

    assert RepositorioUsuariosSqlAlchemy(sesion).roles_de(usuario.id) == frozenset({Rol.DUENO})


def test_us091_ca5_quitar_un_rol_que_no_tiene_no_cambia_nada(sesion: Session, fabrica_sesiones) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))
    with fabrica_sesiones() as escritura:
        repositorio = RepositorioUsuariosSqlAlchemy(escritura)
        repositorio.asignar_rol(usuario.id, Rol.DUENO)
        repositorio.quitar_rol(usuario.id, Rol.RECEPCIONISTA)
        escritura.commit()

    assert RepositorioUsuariosSqlAlchemy(sesion).roles_de(usuario.id) == frozenset({Rol.DUENO})


def test_us091_ca1_la_base_rechaza_un_rol_fuera_de_la_lista(sesion: Session) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))
    sesion.add(UsuarioRolModelo(usuario_id=usuario.id, rol="administrador"))

    with pytest.raises(IntegrityError):
        sesion.commit()
    sesion.rollback()

    assert RepositorioUsuariosSqlAlchemy(sesion).roles_de(usuario.id) == frozenset()


def test_us091_ca4_el_profesional_se_vincula_a_un_usuario_y_el_vinculo_no_se_repite(
    sesion: Session,
) -> None:
    consultorio = un_consultorio(sesion)
    usuario = un_usuario(sesion, consultorio)

    vinculado = un_profesional(sesion, consultorio, usuario_id=usuario.id, matricula="MP 0000")
    sin_vinculo_a = un_profesional(sesion, consultorio)
    sin_vinculo_b = un_profesional(sesion, consultorio)

    assert vinculado.usuario_id == usuario.id
    assert sin_vinculo_a.usuario_id is None and sin_vinculo_b.usuario_id is None
    with pytest.raises(IntegrityError):
        un_profesional(sesion, consultorio, usuario_id=usuario.id)
    sesion.rollback()


def test_us093_ca1_del_consultorio_devuelve_activos_e_inactivos_por_id(sesion: Session) -> None:
    consultorio, otro_consultorio = un_consultorio(sesion), un_consultorio(sesion)
    primero = un_usuario(sesion, consultorio)
    inactivo = un_usuario(sesion, consultorio, activo=False)
    tercero = un_usuario(sesion, consultorio)
    un_usuario(sesion, otro_consultorio)

    usuarios = RepositorioUsuariosSqlAlchemy(sesion).del_consultorio(consultorio.id)

    assert [u.id for u in usuarios] == sorted([primero.id, inactivo.id, tercero.id])
    assert [u.activo for u in usuarios] == [True, False, True]
    assert all(isinstance(u, DatosUsuario) for u in usuarios)


def test_us093_ca1_del_consultorio_sin_usuarios_devuelve_una_lista_vacia(sesion: Session) -> None:
    assert RepositorioUsuariosSqlAlchemy(sesion).del_consultorio(un_consultorio(sesion).id) == []


def test_us093_ca3_guardar_actualiza_activo_y_token_version(sesion: Session, fabrica_sesiones) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion), token_version=2)
    with fabrica_sesiones() as escritura:
        repositorio = RepositorioUsuariosSqlAlchemy(escritura)
        devuelto = repositorio.guardar(replace(repositorio.obtener(usuario.id), activo=False, token_version=3))
        escritura.commit()

    with fabrica_sesiones() as lectura:
        leido = RepositorioUsuariosSqlAlchemy(lectura).obtener(usuario.id)

    assert (leido.activo, leido.token_version) == (False, 3)
    assert devuelto == leido
    assert leido.email == usuario.email and leido.hash_password == usuario.hash_password


def test_us093_ca3_guardar_no_toca_a_los_demas_usuarios(sesion: Session, fabrica_sesiones) -> None:
    consultorio = un_consultorio(sesion)
    editado, vecino = un_usuario(sesion, consultorio), un_usuario(sesion, consultorio, token_version=5)
    with fabrica_sesiones() as escritura:
        repositorio = RepositorioUsuariosSqlAlchemy(escritura)
        repositorio.guardar(replace(repositorio.obtener(editado.id), activo=False))
        escritura.commit()

    leido = RepositorioUsuariosSqlAlchemy(sesion).obtener(vecino.id)

    assert (leido.activo, leido.token_version) == (True, 5)


def test_us093_ca1_reemplazar_roles_deja_exactamente_los_pedidos(sesion: Session, fabrica_sesiones) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion), roles=(Rol.RECEPCIONISTA, Rol.DUENO))
    with fabrica_sesiones() as escritura:
        RepositorioUsuariosSqlAlchemy(escritura).reemplazar_roles(usuario.id, frozenset({Rol.DUENO, Rol.ODONTOLOGO}))
        escritura.commit()

    assert RepositorioUsuariosSqlAlchemy(sesion).roles_de(usuario.id) == frozenset({Rol.DUENO, Rol.ODONTOLOGO})


def test_us093_ca1_reemplazar_roles_no_toca_los_de_otro_usuario(sesion: Session, fabrica_sesiones) -> None:
    consultorio = un_consultorio(sesion)
    uno = un_usuario(sesion, consultorio, roles=(Rol.RECEPCIONISTA,))
    otro = un_usuario(sesion, consultorio, roles=(Rol.RECEPCIONISTA,))
    with fabrica_sesiones() as escritura:
        RepositorioUsuariosSqlAlchemy(escritura).reemplazar_roles(uno.id, frozenset({Rol.DUENO}))
        escritura.commit()

    repositorio = RepositorioUsuariosSqlAlchemy(sesion)

    assert repositorio.roles_de(uno.id) == frozenset({Rol.DUENO})
    assert repositorio.roles_de(otro.id) == frozenset({Rol.RECEPCIONISTA})


def test_us093_ca4_odontologos_activos_no_cuenta_a_los_inactivos(sesion: Session) -> None:
    consultorio, otro_consultorio = un_consultorio(sesion), un_consultorio(sesion)
    activo = un_usuario(sesion, consultorio, roles=(Rol.ODONTOLOGO, Rol.DUENO))
    un_usuario(sesion, consultorio, activo=False, roles=(Rol.ODONTOLOGO,))
    un_usuario(sesion, consultorio, roles=(Rol.RECEPCIONISTA,))
    un_usuario(sesion, otro_consultorio, roles=(Rol.ODONTOLOGO,))

    assert RepositorioUsuariosSqlAlchemy(sesion).odontologos_activos(consultorio.id) == frozenset({activo.id})


def test_us093_ca4_bloquear_administracion_no_falla_en_sqlite(sesion: Session) -> None:
    consultorio = un_consultorio(sesion)

    RepositorioUsuariosSqlAlchemy(sesion).bloquear_administracion(consultorio.id)
    RepositorioUsuariosSqlAlchemy(sesion).bloquear_administracion(consultorio.id)
