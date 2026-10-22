"""Esquemas HTTP de ``/turnos`` (D4), ``/prestaciones`` (C-04) y ``/sillones`` (C-05). Es la única capa que conoce Pydantic."""
from datetime import datetime
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, StringConstraints, field_validator

from app.application.usuarios import UsuarioConRoles
from app.domain.acceso.roles import Rol
from app.domain.agenda.nombres import normalizar_espacios
from app.domain.agenda.prestaciones import DatosPrestacion
from app.domain.agenda.sillones import DatosSillon
from app.domain.turnos.eventos import EventoTurno
from app.domain.turnos.turno import Turno


class CrearTurnoEntrada(BaseModel):
    """Cuerpo de la petición. No valida la zona de ``inicio``: eso es del caso de uso (D6)."""

    model_config = ConfigDict(
        extra="forbid",
        # Ejemplo para /docs: identificadores de la demo (D19).
        json_schema_extra={
            "examples": [{"paciente_id": 1, "prestacion_id": 1, "inicio": "2026-11-02T13:00:00Z"}]
        },
    )

    paciente_id: int
    prestacion_id: int
    inicio: datetime
    profesional_id: int | None = None
    sillon_id: int | None = None


class TurnoSalida(BaseModel):
    """Respuesta ``201``: los once campos del turno creado."""

    id: int
    consultorio_id: int
    paciente_id: int
    profesional_id: int
    sillon_id: int
    prestacion_id: int
    inicio: datetime
    fin: datetime
    duracion_minutos: int
    estado: str
    creado_en: datetime

    @classmethod
    def desde_turno(cls, turno: Turno) -> "TurnoSalida":
        return cls(
            id=turno.id,
            consultorio_id=turno.consultorio_id,
            paciente_id=turno.paciente_id,
            profesional_id=turno.profesional_id,
            sillon_id=turno.sillon_id,
            prestacion_id=turno.prestacion_id,
            inicio=turno.inicio,
            fin=turno.fin,
            duracion_minutos=turno.duracion_minutos,
            estado=turno.estado.value,
            creado_en=turno.creado_en,
        )


class EventoTurnoSalida(BaseModel):
    """Un evento del historial del turno: los nueve campos del modelo (``04``, EventoTurno)."""

    id: int
    turno_id: int
    tipo: str
    actor_tipo: str
    actor_id: str | None
    ocurrido_en: datetime
    antes: dict[str, object] | None
    despues: dict[str, object] | None
    motivo: str | None

    @classmethod
    def desde_evento(cls, evento: EventoTurno) -> "EventoTurnoSalida":
        return cls(
            id=evento.id,
            turno_id=evento.turno_id,
            tipo=evento.tipo.value,
            actor_tipo=evento.actor_tipo.value,
            actor_id=evento.actor_id,
            ocurrido_en=evento.ocurrido_en,
            antes=evento.antes,
            despues=evento.despues,
            motivo=evento.motivo,
        )


def _nombre_normalizado(nombre: str) -> str:
    """Guarda el nombre sin espacios de más; uno vacío después de normalizar es de formato (design P9)."""
    normalizado = normalizar_espacios(nombre)
    if not normalizado:
        raise ValueError("El nombre no puede estar vacío.")
    return normalizado


NombreNormalizado = Annotated[str, AfterValidator(_nombre_normalizado)]
ColorHexadecimal = Annotated[str, Field(pattern=r"^#[0-9A-Fa-f]{6}$")]


class EntradaDeEdicion(BaseModel):
    """Base de los ``PATCH`` de los catálogos: un ``null`` explícito es de formato (D178)."""

    @field_validator("*", mode="before")
    @classmethod
    def _sin_nulos(cls, valor: Any) -> Any:
        # Solo corre con los campos que llegan: un campo omitido no se valida ni entra en
        # ``model_fields_set``; un ``null`` explícito se rechaza nombrando el campo (V2).
        if valor is None:
            raise ValueError("El campo no admite null; omitilo para no cambiarlo.")
        return valor


class CrearPrestacionEntrada(BaseModel):
    """Cuerpo de ``POST /prestaciones``. La duración la valida el dominio (RN-AG-01), no Pydantic."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"nombre": "Blanqueamiento", "duracion_minutos": 60, "color": "#3A7BD5"}]
        },
    )

    nombre: NombreNormalizado
    duracion_minutos: int
    color: ColorHexadecimal
    reservable_online: bool = False


class EditarPrestacionEntrada(EntradaDeEdicion):
    """Cuerpo de ``PATCH /prestaciones/{id}``: todo opcional; un ``null`` explícito es de formato."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"color": "#112233"}]},
    )

    nombre: NombreNormalizado | None = None
    duracion_minutos: int | None = None
    color: ColorHexadecimal | None = None
    reservable_online: bool | None = None
    activa: bool | None = None


class PrestacionSalida(BaseModel):
    """Una prestación del catálogo, sin ``consultorio_id`` (en la v1 hay un solo consultorio, P3)."""

    id: int
    nombre: str
    duracion_minutos: int
    color: str
    reservable_online: bool
    activa: bool

    @classmethod
    def desde_datos(cls, datos: DatosPrestacion) -> "PrestacionSalida":
        assert datos.id is not None
        return cls(
            id=datos.id,
            nombre=datos.nombre,
            duracion_minutos=datos.duracion_minutos,
            color=datos.color,
            reservable_online=datos.reservable_online,
            activa=datos.activa,
        )


class CrearSillonEntrada(BaseModel):
    """Cuerpo de ``POST /sillones``: solo el nombre; el sillón nace activo (``activo`` es campo de más)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"nombre": "Sillón 2"}]},
    )

    nombre: NombreNormalizado


class EditarSillonEntrada(EntradaDeEdicion):
    """Cuerpo de ``PATCH /sillones/{id}``: ``nombre`` y ``activo``, opcionales; ``{}`` es válido."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"activo": False}]},
    )

    nombre: NombreNormalizado | None = None
    activo: bool | None = None


class SillonSalida(BaseModel):
    """Un sillón del catálogo, sin ``consultorio_id`` (en la v1 hay un solo consultorio, S3)."""

    id: int
    nombre: str
    activo: bool

    @classmethod
    def desde_datos(cls, datos: DatosSillon) -> "SillonSalida":
        assert datos.id is not None
        return cls(id=datos.id, nombre=datos.nombre, activo=datos.activo)


class LoginEntrada(BaseModel):
    """Cuerpo de ``POST /auth/login``. El email no se valida como formato: uno mal escrito es solo inexistente (J12)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"email": "odontologa@consultorio-demo.test", "contrasena": "demo-consultorio-2026"}]
        },
    )

    email: Annotated[str, Field(min_length=1, max_length=254)]
    contrasena: Annotated[str, Field(min_length=1)]


class TokensSalida(BaseModel):
    """Respuesta de ``POST /auth/login``; los nombres siguen RFC 6749 §5.1 (design J12)."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: Annotated[str, Field(min_length=1)]


class AccessSalida(BaseModel):
    """Respuesta de ``POST /auth/refresh``: solo un access nuevo, sin refresh nuevo (D201)."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ConflictoSalida(BaseModel):
    codigo: str
    recurso: str
    recurso_id: int
    turno_id: int


class ReferenciaSalida(BaseModel):
    recurso: str
    recurso_id: int | None
    motivo: str


class ErrorDeCampoSalida(BaseModel):
    campo: str | None
    codigo: str | None
    mensaje: str


class Problema(BaseModel):
    """Cuerpo de todo error (RFC 7807, D4): seis campos comunes y las listas de su ``type``."""

    type: str
    title: str
    status: int
    detail: str
    instance: str
    codigos: list[str]
    conflictos: list[ConflictoSalida] | None = None
    referencias: list[ReferenciaSalida] | None = None
    errores: list[ErrorDeCampoSalida] | None = None


def _recortado(valor: Any) -> Any:
    return valor.strip() if isinstance(valor, str) else valor


def _sin_roles_repetidos(roles: list[Rol]) -> list[Rol]:
    if len(set(roles)) != len(roles):
        raise ValueError("Los roles no pueden repetirse.")
    return roles


# Formato mínimo del email (D245): una sola @ con texto a los dos lados y sin espacios, hasta 254
# caracteres. Sin EmailStr: pide una dependencia nueva y rechaza el dominio .test de la demo.
EmailDeUsuario = Annotated[
    str,
    BeforeValidator(_recortado),
    StringConstraints(min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+$"),
]
# Al menos un rol, sin repetir, de los tres válidos (D244).
RolesDeUsuario = Annotated[
    list[Rol], Field(min_length=1, max_length=len(Rol)), AfterValidator(_sin_roles_repetidos)
]


class CrearUsuarioEntrada(BaseModel):
    """Cuerpo de ``POST /usuarios``. El largo de la contraseña lo valida el dominio (RN-AU-07), no Pydantic."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "email": "turnos@consultorio-demo.test",
                    "contrasena": "clave-ficticia-2026",
                    "roles": ["recepcionista"],
                }
            ]
        },
    )

    email: EmailDeUsuario
    contrasena: str
    roles: RolesDeUsuario


class EditarUsuarioEntrada(EntradaDeEdicion):
    """Cuerpo de ``PATCH /usuarios/{id}``: ``roles`` y/o ``activo``; el email y la contraseña no se editan."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"roles": ["recepcionista", "dueno"]}]})

    roles: RolesDeUsuario | None = None
    activo: bool | None = None


class UsuarioSalida(BaseModel):
    """Un usuario del consultorio; nunca el hash, ``token_version``, ``consultorio_id`` ni ``creado_en``."""

    id: int
    email: str
    roles: list[Rol]
    activo: bool

    @classmethod
    def desde_usuario(cls, usuario: UsuarioConRoles) -> "UsuarioSalida":
        assert usuario.datos.id is not None
        return cls(
            id=usuario.datos.id,
            email=usuario.datos.email,
            roles=[rol for rol in Rol if rol in usuario.roles],  # en el orden del enum, no el de la base
            activo=usuario.datos.activo,
        )
