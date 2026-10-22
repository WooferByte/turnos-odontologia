"""Casos de uso de la administración de usuarios (US-093; RN-AU-06, RN-AU-07, RN-AU-08). Sin ``commit()`` ni SQL."""
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from app.application.puertos import EmailRepetidoEnLaBase, HasherDeContrasenas, UnidadDeTrabajo
from app.domain.acceso.roles import Rol
from app.domain.acceso.usuarios import DatosUsuario, normalizar_email, validar_contrasena_inicial
from app.domain.errors import EmailRepetido


@dataclass(frozen=True)
class UsuarioConRoles:
    """El usuario tal como lo guarda la base y sus roles de ahora."""

    datos: DatosUsuario
    roles: frozenset[Rol]


@dataclass(frozen=True)
class CrearUsuarioComando:
    email: str
    contrasena: str
    roles: frozenset[Rol]


def listar_usuarios(uow: UnidadDeTrabajo) -> list[UsuarioConRoles]:
    """Todos los del consultorio, activos e inactivos, por ``id``."""
    with uow:
        usuarios = uow.usuarios.del_consultorio(uow.usuarios.consultorio_unico())
        return [UsuarioConRoles(u, uow.usuarios.roles_de(u.id)) for u in usuarios]


def crear_usuario(
    comando: CrearUsuarioComando,
    uow: UnidadDeTrabajo,
    hasher: HasherDeContrasenas,
    reloj: Callable[[], datetime],
) -> UsuarioConRoles:
    """Valida la contraseña (RN-AU-07), rechaza el email repetido (RN-AU-08) y guarda solo el hash.

    No toca ``profesional`` (D46, US-093 CA-8).
    """
    validar_contrasena_inicial(comando.contrasena)
    email = normalizar_email(comando.email)
    with uow:
        if uow.usuarios.por_email(email) is not None:
            raise EmailRepetido()
        # Hasta acá solo hubo lecturas: hashear no retiene ningún bloqueo de escritura (V2).
        nuevo = DatosUsuario(
            id=None,
            consultorio_id=uow.usuarios.consultorio_unico(),
            email=email,
            hash_password=hasher.hashear(comando.contrasena),
            activo=True,
            token_version=0,
            creado_en=reloj(),
        )
        try:
            creado = uow.usuarios.agregar(nuevo)
        except EmailRepetidoEnLaBase as error:
            # Carrera de dos altas con el mismo email: la restricción UNIQUE de la base (U7).
            raise EmailRepetido() from error
        uow.usuarios.reemplazar_roles(creado.id, comando.roles)
        return UsuarioConRoles(creado, comando.roles)
