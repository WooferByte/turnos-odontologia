"""El usuario del panel y la normalización de su email. Solo biblioteca estándar (regla dura 3, design J5)."""
from dataclasses import dataclass
from datetime import datetime

from app.domain.errors import (
    AdministracionSinOdontologo,
    ContrasenaFueraDeRango,
    EntradaInvalida,
    RestablecerLaPropia,
)

MINIMO_DE_CARACTERES_DE_CONTRASENA = 10  # RN-AU-07
MAXIMO_DE_BYTES_DE_CONTRASENA = 72  # límite de bcrypt (J6)


@dataclass(frozen=True)
class DatosUsuario:
    """El usuario completo, tal como lo guarda la base; ``hash_password`` nunca es la contraseña."""

    id: int | None
    consultorio_id: int
    email: str
    hash_password: str
    activo: bool
    token_version: int
    creado_en: datetime


def normalizar_email(texto: str) -> str:
    """Sin espacios en los extremos y en minúsculas (D199): la forma en que se guarda y se busca."""
    return texto.strip().lower()


def validar_largo_de_contrasena(texto: str, campo: str) -> None:
    """Al menos 10 caracteres y como máximo 72 bytes en UTF-8; no recorta nada (RN-AU-07, D242, K3).

    Una sola regla para la contraseña inicial, la restablecida y la cambiada; ``campo`` nombra el campo del cuerpo.
    """
    if len(texto) < MINIMO_DE_CARACTERES_DE_CONTRASENA or len(texto.encode("utf-8")) > MAXIMO_DE_BYTES_DE_CONTRASENA:
        raise EntradaInvalida((ContrasenaFueraDeRango(campo),))


def validar_contrasena_inicial(texto: str) -> None:
    """La contraseña del alta (campo ``contrasena``), con la regla general de ``validar_largo_de_contrasena``."""
    validar_largo_de_contrasena(texto, "contrasena")


def exigir_no_restablecer_la_propia(actor_id: int, usuario_id: int) -> None:
    """Nadie restablece su propia contraseña: se cambia pidiendo la actual (RN-AU-10, D293)."""
    if actor_id == usuario_id:
        raise RestablecerLaPropia()


def exigir_no_desactivarse(actor_id: int, usuario_id: int, activo_pedido: bool | None) -> None:
    """Nadie se desactiva a sí mismo, aunque haya otros odontólogos (RN-AU-06, D44, D247)."""
    if activo_pedido is False and actor_id == usuario_id:
        raise AdministracionSinOdontologo("Nadie puede desactivarse a sí mismo.")


def exigir_que_quede_un_odontologo(odontologos_activos_despues: int) -> None:
    """El consultorio no puede quedar sin un odontólogo activo (RN-AU-06, D44)."""
    if odontologos_activos_despues == 0:
        raise AdministracionSinOdontologo("El consultorio no puede quedar sin un odontólogo activo.")
