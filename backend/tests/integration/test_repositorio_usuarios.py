"""Repositorio de usuarios sobre SQLite en memoria (US-090 CA-4 borde; RN-AU-03; design J3, J6)."""
from dataclasses import replace

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.puertos import EmailRepetidoEnLaBase
from app.domain.acceso.usuarios import DatosUsuario
from app.infrastructure.db.modelos import UsuarioModelo
from app.infrastructure.repositories.usuarios import RepositorioUsuariosSqlAlchemy
from tests.conftest import RELOJ_FIJO
from tests.factories import un_consultorio

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
