"""Hasher de contraseñas con bcrypt (design J6). El hash lleva su sal y su costo; nunca se guarda la contraseña."""
from functools import cache

import bcrypt

from app.domain.acceso.usuarios import MAXIMO_DE_BYTES_DE_CONTRASENA

MAXIMO_DE_BYTES = MAXIMO_DE_BYTES_DE_CONTRASENA  # bcrypt 5 levanta ValueError con más; nunca puede coincidir con un hash guardado


@cache
def _hash_de_relleno(rondas: int) -> str:
    """Un hash de relleno por costo y por proceso: crear la app no paga bcrypt cada vez (design J8)."""
    return bcrypt.hashpw(b"relleno-para-igualar-tiempos", bcrypt.gensalt(rondas)).decode("ascii")


class HasherBcrypt:
    def __init__(self, rondas: int = 12) -> None:
        self._rondas = rondas
        # Hash de relleno con el mismo costo: el email inexistente tarda lo mismo que el existente (J8).
        self._hash_de_relleno = _hash_de_relleno(rondas)

    def hashear(self, contrasena: str) -> str:
        return bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt(self._rondas)).decode("ascii")

    def verificar(self, contrasena: str, hash_guardado: str) -> bool:
        binaria = contrasena.encode("utf-8")
        if len(binaria) > MAXIMO_DE_BYTES:
            return False
        return bcrypt.checkpw(binaria, hash_guardado.encode("ascii"))

    def verificar_sin_usuario(self, contrasena: str) -> bool:
        """Hace la misma comparación contra el hash de relleno y siempre da ``False``."""
        self.verificar(contrasena, self._hash_de_relleno)
        return False
