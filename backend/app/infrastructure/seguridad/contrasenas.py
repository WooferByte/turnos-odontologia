"""Hasher de contraseñas con bcrypt (design J6). El hash lleva su sal y su costo; nunca se guarda la contraseña."""
import bcrypt

MAXIMO_DE_BYTES = 72  # bcrypt 5 levanta ValueError con más; nunca puede coincidir con un hash guardado


class HasherBcrypt:
    def __init__(self, rondas: int = 12) -> None:
        self._rondas = rondas
        # Hash de relleno con el mismo costo: el email inexistente tarda lo mismo que el existente (J8).
        self._hash_de_relleno = self.hashear("relleno-para-igualar-tiempos")

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
