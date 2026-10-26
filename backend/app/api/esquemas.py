"""Esquemas HTTP de ``/turnos`` (D4), ``/prestaciones`` (C-04), ``/sillones`` (C-05) y ``/bloqueos`` (C-13). Es la única capa que conoce Pydantic."""
from datetime import datetime, time
from typing import Annotated, Any

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.application.bloqueos import BloqueoCreado, BloqueosDelConsultorio
from app.application.horario import HorarioDelProfesional
from app.application.usuarios import UsuarioConRoles
from app.domain.acceso.roles import Rol
from app.domain.agenda.bloqueos import DatosBloqueo
from app.domain.agenda.horario import Franja
from app.domain.agenda.nombres import normalizar_espacios
from app.domain.agenda.prestaciones import DatosPrestacion
from app.domain.agenda.profesionales import DatosProfesional
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


class CambiarContrasenaEntrada(BaseModel):
    """Cuerpo de ``POST /auth/cambiar-contrasena``. La actual es una credencial a comparar, no se valida su largo (K7)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"contrasena_actual": "demo-consultorio-2026", "contrasena_nueva": "clave-nueva-2026"}]
        },
    )

    contrasena_actual: Annotated[str, Field(min_length=1)]
    contrasena_nueva: str


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
    bloqueo_id: int | None = None  # solo en el 422 de RN-AG-04b (D280)


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


class RestablecerContrasenaEntrada(BaseModel):
    """Cuerpo de ``POST /usuarios/{id}/restablecer-contrasena``. El largo lo valida el dominio (RN-AU-07)."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"contrasena": "clave-nueva-2026"}]})

    contrasena: str


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


# --- Horario recurrente (C-12) ---
# Horas como texto «HH:MM» de 00:00 a 23:59 (design H4): la salida es siempre 09:00 y nunca 09:00:00.
HoraDelDia = Annotated[str, Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")]
MAXIMO_DE_FRANJAS = 70  # tope de tamaño del pedido, no por día (D268)


class FranjaEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dia_semana: Annotated[int, Field(ge=0, le=6)]
    hora_inicio: HoraDelDia
    hora_fin: HoraDelDia

    def a_dominio(self) -> Franja:
        return Franja(
            dia_semana=self.dia_semana,
            hora_inicio=time.fromisoformat(self.hora_inicio),
            hora_fin=time.fromisoformat(self.hora_fin),
        )


class ReemplazarHorarioEntrada(BaseModel):
    """Cuerpo de ``PUT /profesionales/{id}/horario``: la lista completa de franjas (puede estar vacía)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "franjas": [
                        {"dia_semana": 0, "hora_inicio": "09:00", "hora_fin": "13:00"},
                        {"dia_semana": 0, "hora_inicio": "15:00", "hora_fin": "19:00"},
                    ]
                }
            ]
        },
    )

    franjas: Annotated[list[FranjaEntrada], Field(max_length=MAXIMO_DE_FRANJAS)]


class FranjaSalida(BaseModel):
    dia_semana: int
    hora_inicio: str
    hora_fin: str


class HorarioSalida(BaseModel):
    profesional_id: int
    zona_horaria: str
    franjas: list[FranjaSalida]

    @classmethod
    def desde_horario(cls, horario: HorarioDelProfesional) -> "HorarioSalida":
        return cls(
            profesional_id=horario.profesional_id,
            zona_horaria=horario.zona_horaria,
            franjas=[
                FranjaSalida(
                    dia_semana=f.dia_semana,
                    hora_inicio=f.hora_inicio.strftime("%H:%M"),
                    hora_fin=f.hora_fin.strftime("%H:%M"),
                )
                for f in horario.franjas
            ],
        )


class ProfesionalSalida(BaseModel):
    id: int
    nombre: str
    activo: bool

    @classmethod
    def desde_datos(cls, datos: DatosProfesional) -> "ProfesionalSalida":
        return cls(id=datos.id, nombre=datos.nombre, activo=datos.activo)


# --- Bloqueos puntuales (C-13) ---
MAXIMO_DEL_MOTIVO = 200  # tope de tamaño del cuerpo, como el de las franjas (D283)


def _motivo_normalizado(motivo: str) -> str:
    """Guarda el motivo sin espacios de más; de 1 a 200 caracteres después de normalizar (D283)."""
    normalizado = _nombre_normalizado(motivo)
    if len(normalizado) > MAXIMO_DEL_MOTIVO:
        raise ValueError(f"El motivo no puede tener más de {MAXIMO_DEL_MOTIVO} caracteres.")
    return normalizado


MotivoDelBloqueo = Annotated[str, AfterValidator(_motivo_normalizado)]


class CrearBloqueoEntrada(BaseModel):
    """Cuerpo de ``POST /bloqueos``. La zona de las fechas y las referencias las valida el dominio (RN-GL-01, RN-GL-04).

    ``profesional_id`` y ``sillon_id`` a la vez son de formato (D272); sin ninguno, bloquea todo el consultorio.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "profesional_id": 1,
                    "inicio": "2026-11-09T03:00:00Z",
                    "fin": "2026-11-14T03:00:00Z",
                    "motivo": "Vacaciones",
                }
            ]
        },
    )

    inicio: datetime
    fin: datetime
    motivo: MotivoDelBloqueo
    profesional_id: int | None = None
    sillon_id: int | None = None

    @model_validator(mode="after")
    def _un_solo_recurso(self) -> "CrearBloqueoEntrada":
        if self.profesional_id is not None and self.sillon_id is not None:
            raise ValueError("Un bloqueo es del profesional, del sillón o de todo el consultorio, no de dos a la vez.")
        return self


class BloqueoSalida(BaseModel):
    """Un bloqueo: el ``alcance`` sale de qué id está presente y no se guarda."""

    id: int
    alcance: str
    profesional_id: int | None
    sillon_id: int | None
    inicio: datetime
    fin: datetime
    motivo: str
    creado_por: int

    @classmethod
    def desde_datos(cls, datos: DatosBloqueo) -> "BloqueoSalida":
        assert datos.id is not None
        return cls(
            id=datos.id,
            alcance=datos.alcance.value,
            profesional_id=datos.profesional_id,
            sillon_id=datos.sillon_id,
            inicio=datos.inicio,
            fin=datos.fin,
            motivo=datos.motivo,
            creado_por=datos.creado_por,
        )


class TurnoAfectadoSalida(BaseModel):
    """Un turno activo dentro del bloqueo: sin otros datos del paciente que su id (D275, RN-PR-01)."""

    id: int
    inicio: datetime
    fin: datetime
    estado: str
    profesional_id: int
    sillon_id: int
    paciente_id: int

    @classmethod
    def desde_turno(cls, turno: Turno) -> "TurnoAfectadoSalida":
        assert turno.id is not None
        return cls(
            id=turno.id,
            inicio=turno.inicio,
            fin=turno.fin,
            estado=turno.estado.value,
            profesional_id=turno.profesional_id,
            sillon_id=turno.sillon_id,
            paciente_id=turno.paciente_id,
        )


class BloqueoCreadoSalida(BloqueoSalida):
    """Respuesta ``201``: el bloqueo y los turnos activos que quedaron adentro (no se cancelaron, D83)."""

    turnos_afectados: list[TurnoAfectadoSalida]

    @classmethod
    def desde_creado(cls, creado: BloqueoCreado) -> "BloqueoCreadoSalida":
        base = BloqueoSalida.desde_datos(creado.bloqueo)
        return cls(
            **base.model_dump(),
            turnos_afectados=[TurnoAfectadoSalida.desde_turno(t) for t in creado.turnos_afectados],
        )


class BloqueosSalida(BaseModel):
    """Respuesta de ``GET /bloqueos``: la zona del consultorio y todos sus bloqueos, sin filtros (D279)."""

    zona_horaria: str
    bloqueos: list[BloqueoSalida]

    @classmethod
    def desde_bloqueos(cls, lista: BloqueosDelConsultorio) -> "BloqueosSalida":
        return cls(
            zona_horaria=lista.zona_horaria,
            bloqueos=[BloqueoSalida.desde_datos(b) for b in lista.bloqueos],
        )
