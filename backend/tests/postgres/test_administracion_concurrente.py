"""Perfil opcional con PostgreSQL: carreras de la administración de usuarios (US-093 CA-2, CA-4; RN-AU-06, RN-AU-08).

Sin mocks: sesiones, repositorio, unidad de trabajo y casos de uso reales, contra PostgreSQL. Las dos
carreras se fuerzan con el arnés de ``carrera.py``: la ganadora escribe y no confirma; la perdedora
espera en otro hilo (en el bloqueo del consultorio o en ``uq_usuario_email``).
"""
from dataclasses import replace

import pytest
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.usuarios import (
    CrearUsuarioComando,
    EditarUsuarioComando,
    crear_usuario,
    editar_usuario,
)
from app.domain.acceso.roles import Rol, UsuarioDelPanel
from app.domain.acceso.usuarios import DatosUsuario
from app.domain.errors import AdministracionSinOdontologo, EmailRepetido
from app.infrastructure.db.modelos import UsuarioModelo
from app.infrastructure.repositories.usuarios import RepositorioUsuariosSqlAlchemy
from app.infrastructure.seguridad.contrasenas import HasherBcrypt
from app.infrastructure.unidad_de_trabajo import UnidadDeTrabajoSqlAlchemy
from tests.conftest import RELOJ_FIJO, reloj_fijo
from tests.factories import un_consultorio, un_usuario
from tests.postgres.carrera import carrera

pytestmark = pytest.mark.postgres

EMAIL_DE_LA_CARRERA = "carrera@consultorio-demo.test"


@pytest.fixture
def uow(engine: Engine) -> UnidadDeTrabajoSqlAlchemy:
    return UnidadDeTrabajoSqlAlchemy(sessionmaker(bind=engine, expire_on_commit=False))


def odontologos_activos(sesion: Session) -> int:
    sesion.expire_all()
    return sesion.scalar(
        select(func.count()).select_from(UsuarioModelo).where(UsuarioModelo.activo.is_(True))
    )


def test_us093_ca4_dos_odontologos_no_se_desactivan_a_la_vez_uno_al_otro(
    engine: Engine, sesion: Session, uow: UnidadDeTrabajoSqlAlchemy
) -> None:
    consultorio = un_consultorio(sesion)
    ana = un_usuario(sesion, consultorio, roles=(Rol.ODONTOLOGO,))
    beto = un_usuario(sesion, consultorio, roles=(Rol.ODONTOLOGO,))

    def ganadora(sesion_ganadora: Session) -> int:
        """Ana toma el bloqueo, desactiva a Beto y NO confirma."""
        repo = RepositorioUsuariosSqlAlchemy(sesion_ganadora)
        repo.bloquear_administracion(consultorio.id)
        actual = repo.obtener(beto.id)
        repo.guardar(replace(actual, activo=False, token_version=actual.token_version + 1))
        return beto.id

    def perdedora():
        """Beto, ya identificado, pide desactivar a Ana: espera el bloqueo y lee lo que Ana confirmó."""
        actor = UsuarioDelPanel(beto.id, frozenset({Rol.ODONTOLOGO}))
        return editar_usuario(ana.id, EditarUsuarioComando(activo=False), actor, uow)

    with pytest.raises(AdministracionSinOdontologo) as capturado:
        carrera(engine, ganadora, perdedora)

    assert capturado.value.codigo == "RN-AU-06"
    assert odontologos_activos(sesion) == 1
    assert sesion.get(UsuarioModelo, ana.id).activo is True
    assert sesion.get(UsuarioModelo, beto.id).activo is False


def test_us093_ca2_dos_altas_simultaneas_con_el_mismo_email(
    engine: Engine, sesion: Session, uow: UnidadDeTrabajoSqlAlchemy
) -> None:
    consultorio = un_consultorio(sesion)

    def ganadora(sesion_ganadora: Session) -> int:
        """La primera alta inserta con ``flush()`` y NO confirma."""
        creado = RepositorioUsuariosSqlAlchemy(sesion_ganadora).agregar(
            DatosUsuario(
                id=None,
                consultorio_id=consultorio.id,
                email=EMAIL_DE_LA_CARRERA,
                hash_password=HasherBcrypt(4).hashear("clave-de-prueba-1"),
                activo=True,
                token_version=0,
                creado_en=RELOJ_FIJO,
            )
        )
        return creado.id

    def perdedora():
        """La segunda alta no ve la fila sin confirmar: su INSERT espera ``uq_usuario_email``."""
        comando = CrearUsuarioComando(EMAIL_DE_LA_CARRERA, "clave-de-prueba-2", frozenset({Rol.RECEPCIONISTA}))
        return crear_usuario(comando, uow, HasherBcrypt(4), reloj_fijo)

    with pytest.raises(EmailRepetido) as capturado:
        carrera(engine, ganadora, perdedora)

    assert capturado.value.codigo == "RN-AU-08"
    sesion.expire_all()
    assert sesion.scalar(select(func.count()).select_from(UsuarioModelo)) == 1
