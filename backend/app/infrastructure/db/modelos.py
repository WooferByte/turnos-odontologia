"""Modelos ORM del subconjunto del primer change (D130). Estilo SQLAlchemy 2.x."""
from datetime import date, datetime, time

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Index, MetaData, SmallInteger, String, UniqueConstraint, true
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.domain.acceso.roles import Rol
from app.infrastructure.db.tipos import FechaHoraUTC


# Nombres estables para claves y UNIQUE (design I4): las migraciones los necesitan.
# Sin clave "ck": las CHECK y los índices ya tienen nombre explícito.
CONVENCION_DE_NOMBRES = {
    "ix": "ix_%(column_0_label)s",
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCION_DE_NOMBRES)


def _fk(tabla: str) -> ForeignKey:
    return ForeignKey(f"{tabla}.id", ondelete="RESTRICT")


class ConsultorioModelo(Base):
    __tablename__ = "consultorio"
    __table_args__ = (UniqueConstraint("slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str]
    slug: Mapped[str]
    zona_horaria: Mapped[str] = mapped_column(default="America/Argentina/Buenos_Aires")


class ProfesionalModelo(Base):
    __tablename__ = "profesional"
    # UNIQUE simple: admite varios nulos en PostgreSQL y en SQLite (design R5).
    __table_args__ = (UniqueConstraint("usuario_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    consultorio_id: Mapped[int] = mapped_column(_fk("consultorio"))
    nombre: Mapped[str]
    activo: Mapped[bool] = mapped_column(default=True)
    usuario_id: Mapped[int | None] = mapped_column(_fk("usuario"))
    matricula: Mapped[str | None] = mapped_column(String)  # sin uso todavía (D215)


class FranjaHorariaModelo(Base):
    """Franja semanal de atención de un profesional, en hora del consultorio (US-002; design H3)."""

    __tablename__ = "franja_horaria"
    __table_args__ = (
        CheckConstraint("dia_semana BETWEEN 0 AND 6", name="ck_franja_horaria_dia_semana"),
        CheckConstraint("hora_inicio < hora_fin", name="ck_franja_horaria_inicio_antes_del_fin"),
        CheckConstraint(
            "vigente_desde IS NULL OR vigente_hasta IS NULL OR vigente_hasta >= vigente_desde",
            name="ck_franja_horaria_vigencia",
        ),
        Index("ix_franja_horaria_profesional_dia", "profesional_id", "dia_semana"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    profesional_id: Mapped[int] = mapped_column(_fk("profesional"))
    dia_semana: Mapped[int] = mapped_column(SmallInteger)
    hora_inicio: Mapped[time]
    hora_fin: Mapped[time]
    vigente_desde: Mapped[date | None]
    vigente_hasta: Mapped[date | None]


class BloqueoModelo(Base):
    """Bloqueo puntual de un profesional, de un sillón o de todo el consultorio (US-003; design B3).

    Con ``sillon_id`` y ``profesional_id`` nulos bloquea todo el consultorio; con los dos presentes no es
    válido (D272). El alcance no se guarda: sale de qué id está presente.
    """

    __tablename__ = "bloqueo"
    __table_args__ = (
        CheckConstraint("inicio < fin", name="ck_bloqueo_inicio_antes_de_fin"),
        CheckConstraint(
            "NOT (profesional_id IS NOT NULL AND sillon_id IS NOT NULL)", name="ck_bloqueo_un_solo_recurso"
        ),
        Index("ix_bloqueo_profesional", "profesional_id", "inicio", "fin"),
        Index("ix_bloqueo_sillon", "sillon_id", "inicio", "fin"),
        Index("ix_bloqueo_consultorio", "consultorio_id", "inicio"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    consultorio_id: Mapped[int] = mapped_column(_fk("consultorio"))
    profesional_id: Mapped[int | None] = mapped_column(_fk("profesional"))
    sillon_id: Mapped[int | None] = mapped_column(_fk("sillon"))
    inicio: Mapped[datetime] = mapped_column(FechaHoraUTC)
    fin: Mapped[datetime] = mapped_column(FechaHoraUTC)
    motivo: Mapped[str] = mapped_column(String(200))
    creado_por: Mapped[int] = mapped_column(_fk("usuario"))


class SillonModelo(Base):
    __tablename__ = "sillon"

    id: Mapped[int] = mapped_column(primary_key=True)
    consultorio_id: Mapped[int] = mapped_column(_fk("consultorio"))
    nombre: Mapped[str]
    activo: Mapped[bool] = mapped_column(default=True)


class PrestacionModelo(Base):
    __tablename__ = "prestacion"
    __table_args__ = (
        UniqueConstraint("consultorio_id", "nombre"),
        CheckConstraint("duracion_minutos > 0", name="ck_prestacion_duracion_positiva"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    consultorio_id: Mapped[int] = mapped_column(_fk("consultorio"))
    nombre: Mapped[str]
    duracion_minutos: Mapped[int]
    color: Mapped[str]
    reservable_online: Mapped[bool] = mapped_column(default=False)
    activa: Mapped[bool] = mapped_column(default=True)


class PacienteModelo(Base):
    __tablename__ = "paciente"
    __table_args__ = (Index("ix_paciente_consultorio_telefono", "consultorio_id", "telefono_whatsapp"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    consultorio_id: Mapped[int] = mapped_column(_fk("consultorio"))
    nombre: Mapped[str]
    apellido: Mapped[str]
    telefono_whatsapp: Mapped[str]
    # Nuevo hasta su primer turno atendido (RN-TD-05, D52); el server_default sirve a los INSERT sin la columna (W8).
    es_nuevo: Mapped[bool] = mapped_column(default=True, server_default=true())


class TurnoModelo(Base):
    __tablename__ = "turno"
    __table_args__ = (
        CheckConstraint("inicio < fin", name="ck_turno_inicio_antes_de_fin"),
        CheckConstraint("duracion_minutos > 0", name="ck_turno_duracion_positiva"),
        Index("ix_turno_profesional_inicio_fin", "profesional_id", "inicio", "fin"),
        Index("ix_turno_sillon_inicio_fin", "sillon_id", "inicio", "fin"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    consultorio_id: Mapped[int] = mapped_column(_fk("consultorio"))
    paciente_id: Mapped[int] = mapped_column(_fk("paciente"))
    profesional_id: Mapped[int] = mapped_column(_fk("profesional"))
    sillon_id: Mapped[int] = mapped_column(_fk("sillon"))
    prestacion_id: Mapped[int] = mapped_column(_fk("prestacion"))
    inicio: Mapped[datetime] = mapped_column(FechaHoraUTC)
    fin: Mapped[datetime] = mapped_column(FechaHoraUTC)
    duracion_minutos: Mapped[int]
    estado: Mapped[str] = mapped_column(String)
    creado_en: Mapped[datetime] = mapped_column(FechaHoraUTC)
    creado_por: Mapped[int | None] = mapped_column(_fk("usuario"))  # nula en los turnos anteriores a C-07


class EventoTurnoModelo(Base):
    """Historial inmutable de un turno (RN-AG-11, design H6). Sin CHECK sobre tipo ni actor_tipo."""

    __tablename__ = "evento_turno"
    __table_args__ = (Index("ix_evento_turno_turno_id_ocurrido_en", "turno_id", "ocurrido_en"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    turno_id: Mapped[int] = mapped_column(_fk("turno"))
    tipo: Mapped[str] = mapped_column(String)
    actor_tipo: Mapped[str] = mapped_column(String)
    actor_id: Mapped[str | None] = mapped_column(String)
    ocurrido_en: Mapped[datetime] = mapped_column(FechaHoraUTC)
    antes: Mapped[dict[str, object] | None] = mapped_column(JSON)
    despues: Mapped[dict[str, object] | None] = mapped_column(JSON)
    motivo: Mapped[str | None] = mapped_column(String)


class UsuarioModelo(Base):
    """Usuario del panel (design J3). El email se guarda normalizado (D199); sus roles, en ``usuario_rol``."""

    __tablename__ = "usuario"
    __table_args__ = (UniqueConstraint("email"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    consultorio_id: Mapped[int] = mapped_column(_fk("consultorio"))
    email: Mapped[str]
    hash_password: Mapped[str]
    activo: Mapped[bool] = mapped_column(default=True)
    token_version: Mapped[int] = mapped_column(default=0)
    creado_en: Mapped[datetime] = mapped_column(FechaHoraUTC)


class UsuarioRolModelo(Base):
    """Un rol de un usuario (RN-AU-02, design R5). La PK compuesta impide repetirlo y el CHECK lo acota (D213)."""

    __tablename__ = "usuario_rol"
    __table_args__ = (
        CheckConstraint(
            "rol IN (" + ", ".join(f"'{rol.value}'" for rol in Rol) + ")",
            name="ck_usuario_rol_rol_valido",
        ),
    )

    usuario_id: Mapped[int] = mapped_column(_fk("usuario"), primary_key=True)
    rol: Mapped[str] = mapped_column(String, primary_key=True)
