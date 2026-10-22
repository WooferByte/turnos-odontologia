"""Casos de uso de la administración de usuarios (US-093; RN-AU-06, RN-AU-07, RN-AU-08). Sin ``commit()`` ni SQL."""
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime

from app.application.puertos import EmailRepetidoEnLaBase, HasherDeContrasenas, UnidadDeTrabajo
from app.domain.acceso.roles import Rol, UsuarioDelPanel
from app.domain.acceso.usuarios import (
    DatosUsuario,
    exigir_no_desactivarse,
    exigir_que_quede_un_odontologo,
    normalizar_email,
    validar_contrasena_inicial,
)
from app.domain.errors import EmailRepetido, UsuarioNoEncontrado


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


@dataclass(frozen=True)
class EditarUsuarioComando:
    """Un campo en ``None`` significa «no cambia»: el ``null`` explícito ya lo rechazó la API (U4)."""

    roles: frozenset[Rol] | None = None
    activo: bool | None = None


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


def _puede_bajar_los_odontologos(comando: EditarUsuarioComando) -> bool:
    """El pedido quita el rol ``odontologo`` o desactiva (RN-AU-06)."""
    quita_el_rol = comando.roles is not None and Rol.ODONTOLOGO not in comando.roles
    return quita_el_rol or comando.activo is False


def editar_usuario(
    usuario_id: int, comando: EditarUsuarioComando, actor: UsuarioDelPanel, uow: UnidadDeTrabajo
) -> UsuarioConRoles:
    """Reemplaza los roles y/o cambia ``activo`` (RN-AU-02, RN-AU-03); todo o nada en una transacción (D252)."""
    with uow:
        actual = uow.usuarios.obtener(usuario_id)
        if actual is None:
            raise UsuarioNoEncontrado(usuario_id)
        if actual.activo and _puede_bajar_los_odontologos(comando):
            # Serializa las ediciones que cuentan odontólogos antes de leer (DD-04, D248).
            uow.usuarios.bloquear_administracion(actual.consultorio_id)
        exigir_no_desactivarse(actor.id, usuario_id, comando.activo)
        if actual.activo and _puede_bajar_los_odontologos(comando):
            activos = uow.usuarios.odontologos_activos(actual.consultorio_id)
            # Un inactivo no cuenta (U10): solo baja la cuenta quien hoy es odontólogo activo.
            if usuario_id in activos:
                exigir_que_quede_un_odontologo(len(activos) - 1)
        if comando.roles is not None:
            uow.usuarios.reemplazar_roles(usuario_id, comando.roles)
        if comando.activo is not None and comando.activo != actual.activo:
            # Solo desactivar corta las sesiones (RN-AU-03); reactivar no revive los tokens viejos.
            version = actual.token_version + 1 if actual.activo else actual.token_version
            actual = uow.usuarios.guardar(replace(actual, activo=comando.activo, token_version=version))
        return UsuarioConRoles(actual, uow.usuarios.roles_de(usuario_id))
