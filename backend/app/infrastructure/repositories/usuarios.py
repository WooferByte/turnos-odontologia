"""Repositorio de usuarios sobre SQLAlchemy. Traduce modelos ORM a tipos de dominio (design J6)."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.puertos import EmailRepetidoEnLaBase
from app.domain.acceso.usuarios import DatosUsuario, normalizar_email
from app.infrastructure.db.modelos import UsuarioModelo

SQLSTATE_UNICIDAD = "23505"  # unique_violation
RESTRICCION_DE_EMAIL = "uq_usuario_email"
MENSAJE_DE_EMAIL_EN_SQLITE = "UNIQUE constraint failed: usuario.email"


def _a_dominio(modelo: UsuarioModelo) -> DatosUsuario:
    return DatosUsuario(
        id=modelo.id,
        consultorio_id=modelo.consultorio_id,
        email=modelo.email,
        hash_password=modelo.hash_password,
        activo=modelo.activo,
        token_version=modelo.token_version,
        creado_en=modelo.creado_en,
    )


def _es_email_repetido(error: IntegrityError) -> bool:
    """Solo la restricción del email; cualquier otra violación sube tal cual."""
    if getattr(error.orig, "sqlstate", None) == SQLSTATE_UNICIDAD:
        restriccion = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        return restriccion == RESTRICCION_DE_EMAIL
    return MENSAJE_DE_EMAIL_EN_SQLITE in str(error.orig)


class RepositorioUsuariosSqlAlchemy:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def por_email(self, email_normalizado: str) -> DatosUsuario | None:
        modelo = self._sesion.scalar(select(UsuarioModelo).where(UsuarioModelo.email == email_normalizado))
        return None if modelo is None else _a_dominio(modelo)

    def obtener(self, usuario_id: int) -> DatosUsuario | None:
        modelo = self._sesion.get(UsuarioModelo, usuario_id)
        return None if modelo is None else _a_dominio(modelo)

    def agregar(self, datos: DatosUsuario) -> DatosUsuario:
        modelo = UsuarioModelo(
            consultorio_id=datos.consultorio_id,
            email=normalizar_email(datos.email),
            hash_password=datos.hash_password,
            activo=datos.activo,
            token_version=datos.token_version,
            creado_en=datos.creado_en,
        )
        self._sesion.add(modelo)
        try:
            self._sesion.flush()  # asigna el id sin confirmar; el commit es de la unidad de trabajo
        except IntegrityError as error:
            if _es_email_repetido(error):
                raise EmailRepetidoEnLaBase() from error
            raise
        return _a_dominio(modelo)
