"""Puertos que la capa de aplicación necesita; los implementa ``infrastructure`` (D12)."""
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

from app.domain.acceso.roles import Rol
from app.domain.acceso.sesion import ClaimsDeSesion
from app.domain.acceso.usuarios import DatosUsuario
from app.domain.agenda.bloqueos import DatosBloqueo
from app.domain.agenda.horario import Franja
from app.domain.agenda.intervalo import Intervalo
from app.domain.agenda.prestaciones import DatosPrestacion
from app.domain.agenda.profesionales import DatosProfesional
from app.domain.agenda.recursos import Paciente, Prestacion, Profesional, Sillon
from app.domain.agenda.sillones import DatosSillon
from app.domain.agenda.solapamiento import TurnoOcupado
from app.domain.turnos.eventos import EventoTurno
from app.domain.turnos.turno import Turno


@dataclass(frozen=True)
class OcupadosEnElIntervalo:
    """Los turnos que intersecan un intervalo, separados por el recurso con el que chocan."""

    del_profesional: Sequence[TurnoOcupado]
    del_sillon: Sequence[TurnoOcupado]


class RepositorioAgenda(Protocol):
    def paciente(self, paciente_id: int) -> Paciente | None: ...

    def prestacion(self, prestacion_id: int) -> Prestacion | None: ...

    def sillon(self, sillon_id: int) -> Sillon | None: ...

    def profesional(self, profesional_id: int) -> Profesional | None: ...

    def profesionales_activos(self, consultorio_id: int) -> Sequence[Profesional]: ...

    def sillones_activos(self, consultorio_id: int) -> Sequence[Sillon]: ...

    def zona_horaria(self, consultorio_id: int) -> str: ...

    def bloquear_recursos(self, profesional_id: int, sillon_id: int) -> None:
        """Toma, hasta que termine la transacción, el bloqueo del profesional y después el del sillón.

        Serializa las reservas del mismo recurso: la segunda espera, y al continuar lee el turno
        que la primera ya confirmó (E11, design I8). El orden es siempre el mismo: así dos
        reservas con recursos cruzados no se interbloquean entre sí.
        """
        ...

    def ocupados_en_el_intervalo(
        self, profesional_id: int, sillon_id: int, intervalo: Intervalo
    ) -> "OcupadosEnElIntervalo":
        """Turnos del profesional y del sillón en cualquier estado, leídos con UNA sentencia.

        La regla la decide el dominio (D12). Una sola lectura evita que una reserva confirmada
        entre dos consultas deje ver un solo choque donde hay dos (E11, design I8).
        """
        ...

    def agregar(self, turno: Turno) -> Turno:
        """Guarda el turno y lo devuelve con su id."""
        ...

    def existe_turno(self, turno_id: int) -> bool: ...

    def turnos_activos_que_intersecan(self, bloqueo: DatosBloqueo) -> Sequence[Turno]:
        """Los turnos activos del alcance del bloqueo (profesional, sillón o consultorio) que lo intersecan.

        Es un recorte por rango, estado y alcance; la regla la confirma el dominio con ``turnos_afectados``.
        """
        ...


class RepositorioBloqueos(Protocol):
    """Bloqueos puntuales del consultorio (US-003; design B2)."""

    def agregar(self, datos: DatosBloqueo) -> DatosBloqueo:
        """Guarda el bloqueo y lo devuelve con su id, sin confirmar."""
        ...

    def del_consultorio(self, consultorio_id: int) -> Sequence[DatosBloqueo]:
        """Todos los del consultorio, pasados y futuros, por ``(inicio, id)`` (D279)."""
        ...

    def obtener(self, bloqueo_id: int) -> DatosBloqueo | None: ...

    def eliminar(self, bloqueo_id: int) -> None:
        """Borrado físico (D278); no toca turnos."""
        ...

    def que_intersecan(
        self, consultorio_id: int, profesional_id: int, sillon_id: int, intervalo: Intervalo
    ) -> Sequence[DatosBloqueo]:
        """Los bloqueos del profesional, del sillón o de todo el consultorio que intersecan el intervalo."""
        ...


class RepositorioHistorial(Protocol):
    """Historial de solo inserción: registrar y leer, nada más (RN-AG-11, design H7)."""

    def registrar(self, evento: EventoTurno) -> EventoTurno:
        """Guarda el evento y lo devuelve con su id."""
        ...

    def del_turno(self, turno_id: int) -> Sequence[EventoTurno]:
        """Los eventos del turno, por ``ocurrido_en`` y, a igual momento, por orden de registro."""
        ...


class RepositorioPrestaciones(Protocol):
    """Catálogo de prestaciones del consultorio (US-001; design P11)."""

    def consultorio_unico(self) -> int:
        """El id del único consultorio de la instalación (D173); si no hay uno solo, falla."""
        ...

    def del_consultorio(self, consultorio_id: int) -> Sequence[DatosPrestacion]:
        """Las del consultorio, activas e inactivas, por ``id``."""
        ...

    def obtener(self, prestacion_id: int) -> DatosPrestacion | None: ...

    def agregar(self, datos: DatosPrestacion) -> DatosPrestacion:
        """Guarda la prestación y la devuelve con su id; levanta ``NombreRepetidoEnLaBase``."""
        ...

    def guardar(self, datos: DatosPrestacion) -> DatosPrestacion:
        """Actualiza la fila de ``datos.id``; levanta ``NombreRepetidoEnLaBase``."""
        ...


class RepositorioSillones(Protocol):
    """Catálogo de sillones del consultorio (US-004; design S9)."""

    def consultorio_unico(self) -> int:
        """El id del único consultorio de la instalación (D173); si no hay uno solo, falla."""
        ...

    def del_consultorio(self, consultorio_id: int) -> Sequence[DatosSillon]:
        """Los del consultorio, activos e inactivos, por ``id``."""
        ...

    def obtener(self, sillon_id: int) -> DatosSillon | None: ...

    def agregar(self, datos: DatosSillon) -> DatosSillon:
        """Guarda el sillón y lo devuelve con su id."""
        ...

    def guardar(self, datos: DatosSillon) -> DatosSillon:
        """Actualiza la fila de ``datos.id``."""
        ...


class RepositorioHorario(Protocol):
    """Horario recurrente de los profesionales y su lista (US-002; design H2)."""

    def consultorio_unico(self) -> int:
        """El id del único consultorio de la instalación (D173); si no hay uno solo, falla."""
        ...

    def profesionales_del_consultorio(self, consultorio_id: int) -> Sequence[DatosProfesional]:
        """Los del consultorio, activos e inactivos, por ``id`` (D260)."""
        ...

    def profesional(self, profesional_id: int) -> DatosProfesional | None: ...

    def franjas_de(self, profesional_id: int) -> Sequence[Franja]:
        """Todas las franjas del profesional, con su vigencia, por día y hora de inicio."""
        ...

    def reemplazar(self, profesional_id: int, franjas: Sequence[Franja]) -> None:
        """Borra las franjas del profesional e inserta estas, sin confirmar (lo hace la unidad de trabajo)."""
        ...


class RepositorioUsuarios(Protocol):
    """Usuarios del panel (design J6). El email se busca y se guarda normalizado (D199)."""

    def consultorio_unico(self) -> int:
        """El id del único consultorio de la instalación (D173); si no hay uno solo, falla."""
        ...

    def por_email(self, email_normalizado: str) -> DatosUsuario | None: ...

    def obtener(self, usuario_id: int) -> DatosUsuario | None: ...

    def agregar(self, datos: DatosUsuario) -> DatosUsuario:
        """Guarda al usuario con el email normalizado y lo devuelve con su id; levanta ``EmailRepetidoEnLaBase``."""
        ...

    def roles_de(self, usuario_id: int) -> frozenset[Rol]:
        """Los roles del usuario, leídos de la base en cada llamada (RN-AU-02, D102).

        Un rol desconocido en la base es un error de programación (``ValueError``): no se ignora.
        """
        ...

    def asignar_rol(self, usuario_id: int, rol: Rol) -> None:
        """Agrega el rol; levanta ``RolInvalidoEnLaBase`` si ya lo tenía o la base lo rechaza."""
        ...

    def quitar_rol(self, usuario_id: int, rol: Rol) -> None:
        """Quita el rol; si no lo tenía no pasa nada."""
        ...

    def del_consultorio(self, consultorio_id: int) -> list[DatosUsuario]:
        """Todos los usuarios del consultorio, activos e inactivos, ordenados por id (US-093 CA-1)."""
        ...

    def guardar(self, datos: DatosUsuario) -> DatosUsuario:
        """Actualiza ``activo`` y ``token_version`` del usuario existente; el resto no se edita."""
        ...

    def reemplazar_roles(self, usuario_id: int, roles: frozenset[Rol]) -> None:
        """Deja al usuario con exactamente esos roles (RN-AU-02)."""
        ...

    def odontologos_activos(self, consultorio_id: int) -> frozenset[int]:
        """Los ids de los usuarios activos con el rol ``odontologo``; un inactivo no cuenta (RN-AU-06)."""
        ...

    def bloquear_administracion(self, consultorio_id: int) -> None:
        """Serializa las ediciones que pueden bajar los odontólogos activos (DD-04, D248)."""
        ...


class UnidadDeTrabajo(Protocol):
    agenda: RepositorioAgenda
    bloqueos: RepositorioBloqueos
    historial: RepositorioHistorial
    horario: RepositorioHorario
    prestaciones: RepositorioPrestaciones
    sillones: RepositorioSillones
    usuarios: RepositorioUsuarios

    def __enter__(self) -> "UnidadDeTrabajo": ...

    def __exit__(self, tipo, valor, traza) -> None: ...


class SolapamientoEnLaBase(Exception):
    """La base rechazó el alta porque otra transacción ocupó el hueco (RN-AG-10c, design I7).

    No es un error de dominio ni lleva código RN: el caso de uso la reevalúa con el dominio.
    recurso dice qué recurso chocó cuando la base lo informa (rechazo de la restricción de
    exclusión, 23P01); es None cuando no hay dato fiable, como en un interbloqueo (40P01):
    ahí PostgreSQL aborta una de dos transacciones que se esperan y no nombra ninguna restricción.
    """

    def __init__(self, recurso: Literal["profesional", "sillon"] | None = None) -> None:
        self.recurso = recurso
        detalle = f" del {recurso}" if recurso else ""
        super().__init__(f"La base rechazó el turno por solapamiento{detalle}.")


class NombreRepetidoEnLaBase(Exception):
    """La base rechazó el nombre exacto de una prestación (RN-AG-15, design P7).

    No es un error de dominio ni lleva código RN: cubre la carrera de dos altas idénticas
    simultáneas y el caso de uso la convierte en ``NombreDePrestacionRepetido``.
    """

    def __init__(self) -> None:
        super().__init__("La base rechazó el nombre de la prestación porque ya existe.")


class HasherDeContrasenas(Protocol):
    """Hash y comparación de contraseñas; el algoritmo vive en ``infrastructure`` (design J6)."""

    def hashear(self, contrasena: str) -> str: ...

    def verificar(self, contrasena: str, hash_guardado: str) -> bool:
        """``False`` si no coincide, también con una contraseña que ningún hash puede tener."""
        ...

    def verificar_sin_usuario(self, contrasena: str) -> bool:
        """Compara contra un hash de relleno con el mismo costo y siempre da ``False`` (design J8)."""
        ...


class TokenIlegible(Exception):
    """El texto no es un token que este firmador haya emitido: forma, firma, algoritmo o claims.

    No es un error de dominio ni lleva código RN: el caso de uso lo convierte en ``SesionInvalida``.
    """

    def __init__(self) -> None:
        super().__init__("El token no se pudo leer.")


class FirmadorDeTokens(Protocol):
    """Firma y lee los tokens de sesión; no decide la vigencia, eso es del dominio (design J7)."""

    def firmar(self, claims: ClaimsDeSesion) -> str: ...

    def leer(self, token: str) -> ClaimsDeSesion:
        """Levanta ``TokenIlegible`` ante cualquier problema de forma, firma o contenido."""
        ...


class EmailRepetidoEnLaBase(Exception):
    """La base rechazó el email de un usuario porque ya existe (D199, design J3).

    No es un error de dominio ni lleva código RN: en este change solo lo ven el seed y los tests
    (no hay alta de usuarios hasta C-09).
    """

    def __init__(self) -> None:
        super().__init__("La base rechazó el email del usuario porque ya existe.")


class RolInvalidoEnLaBase(Exception):
    """La base rechazó la asignación de un rol: repetido o fuera de la lista cerrada (RN-AU-05, D213).

    No es un error de dominio ni lleva código RN: en este change solo lo ven el seed y los tests
    (no hay asignación de roles por la API hasta C-09).
    """

    def __init__(self) -> None:
        super().__init__("La base rechazó el rol del usuario porque está repetido o no es válido.")
