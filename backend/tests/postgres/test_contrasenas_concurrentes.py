"""Perfil opcional con PostgreSQL: cambios de contraseña simultáneos (US-093 CA-6; RN-AU-03, RN-AU-09; D299).

Sin mocks: sesiones, repositorio, unidad de trabajo y casos de uso reales, contra PostgreSQL. Las carreras
se fuerzan con el arnés de ``carrera.py``: la ganadora toma la fila del usuario, escribe y NO confirma; la
perdedora corre en otro hilo y espera en ``FOR UPDATE`` de ``obtener_para_cambiar``. Sin el bloqueo, la
perdedora leería la versión vieja y dejaría vigentes tokens que la ganadora quería cortar.
"""
from dataclasses import replace
from datetime import timedelta

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.sesion import Vigencias, cambiar_contrasena
from app.application.usuarios import restablecer_contrasena
from app.domain.acceso.roles import Rol, UsuarioDelPanel
from app.domain.errors import ContrasenaActualIncorrecta
from app.infrastructure.db.modelos import UsuarioModelo
from app.infrastructure.repositories.usuarios import RepositorioUsuariosSqlAlchemy
from app.infrastructure.seguridad.contrasenas import HasherBcrypt
from app.infrastructure.seguridad.tokens import FirmadorJwtHs256
from app.infrastructure.unidad_de_trabajo import UnidadDeTrabajoSqlAlchemy
from tests.conftest import SECRETO_DE_PRUEBA, reloj_fijo
from tests.factories import un_consultorio, un_usuario
from tests.postgres.carrera import carrera

pytestmark = pytest.mark.postgres

ACTUAL = "demo-consultorio-2026"
DEL_PRIMER_PEDIDO = "primera-clave-2026"
DEL_SEGUNDO_PEDIDO = "segunda-clave-2026"
HASHER = HasherBcrypt(4)


@pytest.fixture
def uow(engine: Engine) -> UnidadDeTrabajoSqlAlchemy:
    return UnidadDeTrabajoSqlAlchemy(sessionmaker(bind=engine, expire_on_commit=False))


def _leer(engine: Engine, usuario_id: int) -> UsuarioModelo:
    with sessionmaker(bind=engine, expire_on_commit=False)() as lectura:
        return lectura.get_one(UsuarioModelo, usuario_id)


def _escribir_sin_confirmar(usuario_id: int, contrasena: str):
    """La ganadora: toma la fila con ``obtener_para_cambiar``, guarda su hash y su versión y NO confirma."""

    def ganadora(sesion_ganadora: Session) -> int:
        repositorio = RepositorioUsuariosSqlAlchemy(sesion_ganadora)
        actual = repositorio.obtener_para_cambiar(usuario_id)
        repositorio.guardar(
            replace(actual, hash_password=HASHER.hashear(contrasena), token_version=actual.token_version + 1)
        )
        return usuario_id

    return ganadora


def test_us093_ca6_dos_cambios_simultaneos_sobre_el_mismo_usuario_suben_la_version_dos_veces(
    engine: Engine, sesion: Session, uow: UnidadDeTrabajoSqlAlchemy
) -> None:
    consultorio = un_consultorio(sesion)
    odontologa = un_usuario(sesion, consultorio, roles=(Rol.ODONTOLOGO,))
    recepcionista = un_usuario(sesion, consultorio, contrasena=ACTUAL, roles=(Rol.RECEPCIONISTA,))
    actor = UsuarioDelPanel(odontologa.id, frozenset({Rol.ODONTOLOGO}))

    def perdedora() -> None:
        """El segundo restablecimiento espera la fila y lee la versión que confirmó el primero."""
        return restablecer_contrasena(recepcionista.id, DEL_SEGUNDO_PEDIDO, actor, uow, HASHER)

    carrera(engine, _escribir_sin_confirmar(recepcionista.id, DEL_PRIMER_PEDIDO), perdedora)

    guardado = _leer(engine, recepcionista.id)
    assert guardado.token_version == 2  # sin el bloqueo, los dos leen 0 y queda 1
    assert HASHER.verificar(DEL_SEGUNDO_PEDIDO, guardado.hash_password)
    assert not HASHER.verificar(DEL_PRIMER_PEDIDO, guardado.hash_password)


def test_us093_ca6_restablecer_y_cambiar_la_propia_a_la_vez_no_deja_vigente_el_cambio_propio(
    engine: Engine, sesion: Session, uow: UnidadDeTrabajoSqlAlchemy
) -> None:
    consultorio = un_consultorio(sesion)
    recepcionista = un_usuario(sesion, consultorio, contrasena=ACTUAL, roles=(Rol.RECEPCIONISTA,))
    actor = UsuarioDelPanel(recepcionista.id, frozenset({Rol.RECEPCIONISTA}))
    firmador = FirmadorJwtHs256(SECRETO_DE_PRUEBA)
    vigencias = Vigencias(access=timedelta(minutes=15), refresh=timedelta(days=7))

    def perdedora():
        """El cambio propio, con la actual vieja, espera al restablecimiento y la verifica contra el hash nuevo."""
        return cambiar_contrasena(
            actor, ACTUAL, DEL_SEGUNDO_PEDIDO, uow, HASHER, firmador, vigencias, reloj_fijo
        )

    with pytest.raises(ContrasenaActualIncorrecta) as capturado:
        carrera(engine, _escribir_sin_confirmar(recepcionista.id, DEL_PRIMER_PEDIDO), perdedora)

    assert capturado.value.codigo == "RN-AU-09"
    guardado = _leer(engine, recepcionista.id)
    assert guardado.token_version == 1  # sin el bloqueo, el cambio propio verifica la vieja y deja vigentes sus tokens
    assert HASHER.verificar(DEL_PRIMER_PEDIDO, guardado.hash_password)
    assert not HASHER.verificar(ACTUAL, guardado.hash_password)
    assert not HASHER.verificar(DEL_SEGUNDO_PEDIDO, guardado.hash_password)
