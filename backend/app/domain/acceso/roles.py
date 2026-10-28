"""Roles y permisos del panel (RN-AU-02, RN-AU-05, design R3 y R4).

Un usuario tiene uno o más roles y sus permisos son la unión de los de cada rol. La matriz es
datos puros y se lee renglón a renglón igual que la tabla de ``03_actores_y_roles.md``.
"""
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from app.domain.errors import PermisoInsuficiente


class Rol(StrEnum):
    ODONTOLOGO = "odontologo"
    RECEPCIONISTA = "recepcionista"
    DUENO = "dueno"


class Permiso(StrEnum):
    TURNOS_CREAR = "turnos.crear"
    HISTORIAL_LEER = "historial.leer"
    PRESTACIONES_LEER = "prestaciones.leer"
    PRESTACIONES_EDITAR = "prestaciones.editar"
    SILLONES_LEER = "sillones.leer"
    SILLONES_EDITAR = "sillones.editar"
    USUARIOS_LEER = "usuarios.leer"
    USUARIOS_EDITAR = "usuarios.editar"
    HORARIO_LEER = "horario.leer"
    HORARIO_EDITAR = "horario.editar"
    PROFESIONALES_LEER = "profesionales.leer"
    BLOQUEOS_LEER = "bloqueos.leer"
    BLOQUEOS_EDITAR = "bloqueos.editar"
    CONTRASENA_PROPIA = "contrasena.propia"
    SESION_LEER = "sesion.leer"
    TURNOS_LEER = "turnos.leer"


_TODOS = frozenset({Rol.ODONTOLOGO, Rol.RECEPCIONISTA, Rol.DUENO})
_SOLO_EL_ODONTOLOGO = frozenset({Rol.ODONTOLOGO})
_ODONTOLOGO_Y_DUENO = frozenset({Rol.ODONTOLOGO, Rol.DUENO})
_ODONTOLOGO_Y_RECEPCION = frozenset({Rol.ODONTOLOGO, Rol.RECEPCIONISTA})

MATRIZ: Mapping[Permiso, frozenset[Rol]] = {
    Permiso.TURNOS_CREAR: _ODONTOLOGO_Y_RECEPCION,
    Permiso.HISTORIAL_LEER: _TODOS,
    Permiso.PRESTACIONES_LEER: _TODOS,
    Permiso.PRESTACIONES_EDITAR: _SOLO_EL_ODONTOLOGO,
    Permiso.SILLONES_LEER: _TODOS,
    Permiso.SILLONES_EDITAR: _SOLO_EL_ODONTOLOGO,
    Permiso.USUARIOS_LEER: _ODONTOLOGO_Y_DUENO,
    Permiso.USUARIOS_EDITAR: _SOLO_EL_ODONTOLOGO,
    Permiso.HORARIO_LEER: _TODOS,
    Permiso.HORARIO_EDITAR: _SOLO_EL_ODONTOLOGO,
    Permiso.PROFESIONALES_LEER: _TODOS,
    Permiso.BLOQUEOS_LEER: _TODOS,
    Permiso.BLOQUEOS_EDITAR: _SOLO_EL_ODONTOLOGO,
    Permiso.CONTRASENA_PROPIA: _TODOS,
    Permiso.SESION_LEER: _TODOS,
    Permiso.TURNOS_LEER: _TODOS,
}


@dataclass(frozen=True)
class UsuarioDelPanel:
    """Quien hace la petición: su id y los roles leídos de la base en esa misma petición."""

    id: int
    roles: frozenset[Rol]


def puede(roles: frozenset[Rol], permiso: Permiso) -> bool:
    """Unión de roles (RN-AU-02): alcanza con que uno de ellos tenga el permiso."""
    return not roles.isdisjoint(MATRIZ[permiso])


def exigir_permiso(roles: frozenset[Rol], permiso: Permiso) -> None:
    if not puede(roles, permiso):
        raise PermisoInsuficiente()
