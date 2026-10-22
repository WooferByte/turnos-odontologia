"""Repositorio de usuarios sobre SQLAlchemy. Traduce modelos ORM a tipos de dominio (design J6)."""
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.puertos import EmailRepetidoEnLaBase, RolInvalidoEnLaBase
from app.domain.acceso.roles import Rol
from app.domain.acceso.usuarios import DatosUsuario, normalizar_email
from app.infrastructure.db.modelos import ConsultorioModelo, UsuarioModelo, UsuarioRolModelo
from app.infrastructure.repositories.consultorio import consultorio_unico

SQLSTATE_UNICIDAD = "23505"  # unique_violation
RESTRICCION_DE_EMAIL = "uq_usuario_email"
MENSAJE_DE_EMAIL_EN_SQLITE = "UNIQUE constraint failed: usuario.email"
SQLSTATE_CHECK = "23514"  # check_violation
MENSAJES_DE_ROL_EN_SQLITE = ("UNIQUE constraint failed: usuario_rol.", "CHECK constraint failed: ck_usuario_rol_rol_valido")
RESTRICCIONES_DE_ROL = ("pk_usuario_rol", "ck_usuario_rol_rol_valido")


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


def _es_rol_rechazado(error: IntegrityError) -> bool:
    """Solo la PK compuesta (repetido) y el CHECK (inválido); cualquier otra violación sube tal cual."""
    if getattr(error.orig, "sqlstate", None) in (SQLSTATE_UNICIDAD, SQLSTATE_CHECK):
        restriccion = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        return restriccion in RESTRICCIONES_DE_ROL
    return any(mensaje in str(error.orig) for mensaje in MENSAJES_DE_ROL_EN_SQLITE)


class RepositorioUsuariosSqlAlchemy:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def consultorio_unico(self) -> int:
        return consultorio_unico(self._sesion)

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

    def roles_de(self, usuario_id: int) -> frozenset[Rol]:
        filas = self._sesion.scalars(select(UsuarioRolModelo.rol).where(UsuarioRolModelo.usuario_id == usuario_id))
        return frozenset(Rol(fila) for fila in filas)  # ValueError ante un rol desconocido

    def asignar_rol(self, usuario_id: int, rol: Rol) -> None:
        self._sesion.add(UsuarioRolModelo(usuario_id=usuario_id, rol=rol.value))
        try:
            self._sesion.flush()
        except IntegrityError as error:
            if _es_rol_rechazado(error):
                raise RolInvalidoEnLaBase() from error
            raise

    def quitar_rol(self, usuario_id: int, rol: Rol) -> None:
        self._sesion.execute(
            delete(UsuarioRolModelo).where(
                UsuarioRolModelo.usuario_id == usuario_id, UsuarioRolModelo.rol == rol.value
            )
        )

    def del_consultorio(self, consultorio_id: int) -> list[DatosUsuario]:
        modelos = self._sesion.scalars(
            select(UsuarioModelo).where(UsuarioModelo.consultorio_id == consultorio_id).order_by(UsuarioModelo.id)
        )
        return [_a_dominio(modelo) for modelo in modelos]

    def guardar(self, datos: DatosUsuario) -> DatosUsuario:
        modelo = self._sesion.get_one(UsuarioModelo, datos.id)
        modelo.activo = datos.activo
        modelo.token_version = datos.token_version
        self._sesion.flush()
        return _a_dominio(modelo)

    def reemplazar_roles(self, usuario_id: int, roles: frozenset[Rol]) -> None:
        actuales = self.roles_de(usuario_id)
        sobrantes = [rol.value for rol in actuales - roles]
        if sobrantes:
            self._sesion.execute(
                delete(UsuarioRolModelo).where(
                    UsuarioRolModelo.usuario_id == usuario_id, UsuarioRolModelo.rol.in_(sobrantes)
                )
            )
        for rol in roles - actuales:
            self.asignar_rol(usuario_id, rol)

    def odontologos_activos(self, consultorio_id: int) -> frozenset[int]:
        ids = self._sesion.scalars(
            select(UsuarioModelo.id)
            .join(UsuarioRolModelo, UsuarioRolModelo.usuario_id == UsuarioModelo.id)
            .where(
                UsuarioModelo.consultorio_id == consultorio_id,
                UsuarioModelo.activo.is_(True),
                UsuarioRolModelo.rol == Rol.ODONTOLOGO.value,
            )
        )
        return frozenset(ids)

    def bloquear_administracion(self, consultorio_id: int) -> None:
        # FOR UPDATE sobre la fila del consultorio: serializa las ediciones que pueden bajar los
        # odontólogos activos (DD-04, D248). SQLite omite la cláusula.
        self._sesion.execute(
            select(ConsultorioModelo.id).where(ConsultorioModelo.id == consultorio_id).with_for_update()
        )
