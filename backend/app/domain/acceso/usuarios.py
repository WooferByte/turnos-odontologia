"""El usuario del panel y la normalización de su email. Solo biblioteca estándar (regla dura 3, design J5)."""
from dataclasses import dataclass
from datetime import datetime


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
