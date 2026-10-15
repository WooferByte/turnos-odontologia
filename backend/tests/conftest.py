"""Fixtures compartidos: una base SQLite en memoria nueva por test (D12, regla dura 6)."""
from collections.abc import Iterator
from datetime import datetime, timedelta

import httpx
import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.acceso.roles import Rol
from app.domain.acceso.sesion import ClaimsDeSesion, TipoDeToken
from app.domain.tiempo import UTC
from app.infrastructure.db.modelos import Base, ConsultorioModelo
from app.infrastructure.db.motor import crear_engine_en_memoria
from app.infrastructure.seguridad.tokens import FirmadorJwtHs256
from app.infrastructure.unidad_de_trabajo import UnidadDeTrabajoSqlAlchemy

RELOJ_FIJO = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)


def reloj_fijo() -> datetime:
    return RELOJ_FIJO


@pytest.fixture
def engine() -> Iterator[Engine]:
    engine = crear_engine_en_memoria()
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def fabrica_sesiones(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def sesion(fabrica_sesiones: sessionmaker[Session]) -> Iterator[Session]:
    with fabrica_sesiones() as sesion:
        yield sesion


@pytest.fixture
def uow(fabrica_sesiones: sessionmaker[Session]) -> UnidadDeTrabajoSqlAlchemy:
    return UnidadDeTrabajoSqlAlchemy(fabrica_sesiones)


DIA_DE_PRUEBA = (2026, 11, 2)  # horario compartido por los tests de agenda


def a_las(hora: int, minuto: int = 0) -> datetime:
    """Instante UTC de ``DIA_DE_PRUEBA`` a esa hora y minuto."""
    return datetime(*DIA_DE_PRUEBA, hora, minuto, tzinfo=UTC)


# Secreto ficticio de los tests de la sesión (C-06, design J10): 32 bytes o más, nunca real.
SECRETO_DE_PRUEBA = "secreto-ficticio-solo-para-los-tests-0123456789"


ROLES_DEL_PANEL = (Rol.ODONTOLOGO, Rol.RECEPCIONISTA)  # cubren todas las rutas del panel (design R17)
VIGENCIA_DE_PRUEBA = timedelta(minutes=15)


def token_de(
    usuario_id: int,
    *,
    token_version: int = 0,
    tipo: TipoDeToken = TipoDeToken.ACCESS,
    emitido_en: datetime = RELOJ_FIJO,
    vigencia: timedelta = VIGENCIA_DE_PRUEBA,
) -> str:
    """Token real firmado con el secreto de los tests; no hay doble del firmador (design R17)."""
    claims = ClaimsDeSesion(
        usuario_id=usuario_id,
        token_version=token_version,
        tipo=tipo,
        emitido_en=emitido_en,
        vence_en=emitido_en + vigencia,
    )
    return FirmadorJwtHs256(SECRETO_DE_PRUEBA).firmar(claims)


def cabecera_de(engine: Engine, roles: tuple[Rol, ...] = ROLES_DEL_PANEL) -> dict[str, str]:
    """Crea un usuario ficticio con esos ``roles`` y devuelve la cabecera con su access token real.

    Usa el único consultorio de la base y, si todavía no hay ninguno, crea uno (``consultorio_unico``
    exige que haya exactamente uno: no se agrega un segundo).
    """
    from tests.factories import un_consultorio, un_usuario  # factories importa este módulo

    with Session(engine, expire_on_commit=False) as sesion:
        consultorio = sesion.scalars(select(ConsultorioModelo)).first() or un_consultorio(sesion)
        usuario = un_usuario(sesion, consultorio, roles=roles)
    return {"Authorization": f"Bearer {token_de(usuario.id)}"}


class TokenDelPanel(httpx.Auth):
    """Autenticación de los clientes de test: crea el usuario y su token en la primera petición.

    Perezosa porque los tests crean su propio consultorio después del *fixture* ``cliente``, y
    ``consultorio_unico`` falla con más de uno. Una cabecera ``Authorization`` explícita en la
    petición manda sobre la de este objeto (design R17).
    """

    def __init__(self, engine: Engine, roles: tuple[Rol, ...] = ROLES_DEL_PANEL) -> None:
        self._engine = engine
        self._roles = roles
        self._cabecera: dict[str, str] | None = None

    def auth_flow(self, request: httpx.Request):
        if "Authorization" not in request.headers:
            if self._cabecera is None:
                self._cabecera = cabecera_de(self._engine, self._roles)
            request.headers["Authorization"] = self._cabecera["Authorization"]
        yield request


def con_token_del_panel(cliente, engine: Engine, roles: tuple[Rol, ...] = ROLES_DEL_PANEL):
    """Hace que el ``TestClient`` mande el access token real de un usuario con esos ``roles``."""
    cliente.auth = TokenDelPanel(engine, roles)
    return cliente
