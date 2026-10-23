"""Perfil opcional con PostgreSQL: migraciones y esquema (INF-1, INF-4)."""
from datetime import time

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import DateTime, Engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.acceso.roles import Rol
from app.infrastructure.db.modelos import Base
from app.infrastructure.db.tipos import FechaHoraUTC
from tests.conftest import a_las
from tests.factories import (
    franja,
    un_consultorio,
    un_evento,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
    un_usuario,
)

TABLAS_DE_C01 = {"consultorio", "profesional", "sillon", "prestacion", "paciente", "turno"}
TABLAS_DEL_MODELO = set(Base.metadata.tables)
TABLAS_HASTA_LOS_ROLES = TABLAS_DEL_MODELO - {"franja_horaria"}  # el esquema de 0007, antes del horario
# Funciones del esquema public que no son de una extensión (btree_gist deja las suyas, D145).
FUNCIONES_DE_LA_APLICACION = text(
    "SELECT p.proname FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
    "WHERE n.nspname = 'public' AND NOT EXISTS "
    "(SELECT 1 FROM pg_depend d WHERE d.objid = p.oid AND d.deptype = 'e')"
)

pytestmark = pytest.mark.postgres


def test_el_perfil_se_conecta_a_postgresql(sesion: Session) -> None:
    assert sesion.execute(text("SELECT 1")).scalar_one() == 1


def test_inf1_base_vacia_migrada_queda_con_el_esquema_del_modelo(engine: Engine) -> None:
    with engine.connect() as conexion:
        inspector = inspect(conexion)
        assert set(inspector.get_table_names()) == TABLAS_DEL_MODELO | {"alembic_version"}
        assert "franja_horaria" in inspector.get_table_names()
        assert "ix_franja_horaria_profesional_dia" in {i["name"] for i in inspector.get_indexes("franja_horaria")}
        assert {c["name"] for c in inspector.get_check_constraints("franja_horaria")} == {
            "ck_franja_horaria_dia_semana",
            "ck_franja_horaria_inicio_antes_del_fin",
            "ck_franja_horaria_vigencia",
        }

        contexto = MigrationContext.configure(conexion, opts={"compare_type": True})
        assert compare_metadata(contexto, Base.metadata) == []

        for tabla in Base.metadata.sorted_tables:
            columnas = {c["name"]: c["type"] for c in inspector.get_columns(tabla.name)}
            for columna in tabla.columns:
                if isinstance(columna.type, (DateTime, FechaHoraUTC)):
                    assert columnas[columna.name].timezone is True, f"{tabla.name}.{columna.name}"


def test_inf1_deshacer_las_migraciones_deja_la_base_vacia(engine: Engine, config_alembic: Config) -> None:
    command.downgrade(config_alembic, "base")

    with engine.connect() as conexion:
        assert set(inspect(conexion).get_table_names()) == {"alembic_version"}
        restricciones = conexion.execute(
            text(
                "SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace "
                "WHERE n.nspname = 'public' AND c.conrelid::regclass::text <> 'alembic_version'"
            )
        ).scalar_one()
        assert restricciones == 0
        assert conexion.execute(FUNCIONES_DE_LA_APLICACION).all() == []

    command.upgrade(config_alembic, "head")

    with engine.connect() as conexion:
        assert set(inspect(conexion).get_table_names()) == TABLAS_DEL_MODELO | {"alembic_version"}


def test_inf1_deshacer_las_migraciones_del_historial_deja_el_esquema_de_c01(
    engine: Engine, config_alembic: Config, sesion: Session
) -> None:
    consultorio = un_consultorio(sesion)
    un_turno(
        sesion,
        paciente=un_paciente(sesion, consultorio),
        profesional=un_profesional(sesion, consultorio),
        sillon=un_sillon(sesion, consultorio),
        prestacion=una_prestacion(sesion, consultorio),
        inicio=a_las(10),
    )
    with engine.connect() as conexion:
        assert "evento_turno" in inspect(conexion).get_table_names()

    command.downgrade(config_alembic, "0002")

    with engine.connect() as conexion:
        assert set(inspect(conexion).get_table_names()) == TABLAS_DE_C01 | {"alembic_version"}
        assert conexion.execute(FUNCIONES_DE_LA_APLICACION).all() == []
    with engine.connect() as conexion:  # SQL directo: el modelo ya tiene columnas que 0002 no conoce
        assert conexion.execute(text("SELECT count(*) FROM turno")).scalar_one() == 1


def test_inf1_la_migracion_0005_completa_las_prestaciones_existentes(
    engine: Engine, config_alembic: Config
) -> None:
    command.downgrade(config_alembic, "0004")
    with engine.begin() as conexion:
        conexion.execute(
            text(
                "INSERT INTO consultorio (id, nombre, slug, zona_horaria) "
                "VALUES (1, 'Consultorio de Prueba', 'consultorio-prueba', 'America/Argentina/Buenos_Aires')"
            )
        )
        conexion.execute(
            text(
                "INSERT INTO prestacion (id, consultorio_id, nombre, duracion_minutos, activa) "
                "VALUES (1, 1, 'Limpieza', 45, true)"
            )
        )

    command.upgrade(config_alembic, "head")

    with engine.connect() as conexion:
        fila = conexion.execute(
            text("SELECT nombre, duracion_minutos, color, reservable_online FROM prestacion")
        ).one()
        assert tuple(fila) == ("Limpieza", 45, "#9E9E9E", False)
        columnas = {c["name"]: c for c in inspect(conexion).get_columns("prestacion")}
        assert columnas["color"]["nullable"] is False
        assert columnas["color"]["default"] is None  # el relleno no queda como default (design P12)
        assert columnas["reservable_online"]["default"] is None

    command.downgrade(config_alembic, "0004")

    with engine.connect() as conexion:
        columnas = {c["name"] for c in inspect(conexion).get_columns("prestacion")}
        assert "color" not in columnas and "reservable_online" not in columnas
        assert conexion.execute(text("SELECT nombre FROM prestacion")).scalar_one() == "Limpieza"


def test_inf1_deshacer_solo_la_migracion_de_usuarios_deja_el_esquema_anterior(
    engine: Engine, config_alembic: Config, sesion: Session
) -> None:
    consultorio = un_consultorio(sesion)
    turno = un_turno(
        sesion,
        paciente=un_paciente(sesion, consultorio),
        profesional=un_profesional(sesion, consultorio),
        sillon=un_sillon(sesion, consultorio),
        prestacion=una_prestacion(sesion, consultorio),
        inicio=a_las(10),
    )
    un_evento(sesion, turno)
    with engine.connect() as conexion:
        assert "usuario" in inspect(conexion).get_table_names()

    command.downgrade(config_alembic, "0005")

    with engine.connect() as conexion:
        assert set(inspect(conexion).get_table_names()) == (
            TABLAS_DEL_MODELO - {"usuario", "usuario_rol", "franja_horaria"}
        ) | {"alembic_version"}
        assert conexion.execute(text("SELECT count(*) FROM turno")).scalar_one() == 1
        assert conexion.execute(text("SELECT count(*) FROM evento_turno")).scalar_one() == 1

    command.upgrade(config_alembic, "head")

    with engine.connect() as conexion:
        assert "usuario" in inspect(conexion).get_table_names()


def test_inf1_deshacer_solo_la_migracion_de_roles_deja_el_esquema_de_la_sesion(
    engine: Engine, config_alembic: Config, sesion: Session
) -> None:
    consultorio = un_consultorio(sesion)
    usuario = un_usuario(sesion, consultorio, roles=(Rol.ODONTOLOGO, Rol.DUENO))
    profesional = un_profesional(sesion, consultorio, usuario_id=usuario.id, matricula="MP 0000")
    turno = un_turno(
        sesion,
        paciente=un_paciente(sesion, consultorio),
        profesional=profesional,
        sillon=un_sillon(sesion, consultorio),
        prestacion=una_prestacion(sesion, consultorio),
        inicio=a_las(10),
        creado_por=usuario.id,
    )
    un_evento(sesion, turno)
    with engine.connect() as conexion:
        assert "usuario_rol" in inspect(conexion).get_table_names()

    command.downgrade(config_alembic, "0006")

    with engine.connect() as conexion:
        inspector = inspect(conexion)
        assert set(inspector.get_table_names()) == (TABLAS_DEL_MODELO - {"usuario_rol", "franja_horaria"}) | {"alembic_version"}
        assert "usuario_id" not in {c["name"] for c in inspector.get_columns("profesional")}
        assert "matricula" not in {c["name"] for c in inspector.get_columns("profesional")}
        assert "creado_por" not in {c["name"] for c in inspector.get_columns("turno")}
        for tabla in ("usuario", "profesional", "turno", "evento_turno"):
            assert conexion.execute(text(f"SELECT count(*) FROM {tabla}")).scalar_one() == 1

    command.upgrade(config_alembic, "head")

    with engine.connect() as conexion:
        assert "usuario_rol" in inspect(conexion).get_table_names()
        assert "creado_por" in {c["name"] for c in inspect(conexion).get_columns("turno")}


def test_us091_ca1_la_base_rechaza_un_rol_invalido(sesion: Session) -> None:
    usuario = un_usuario(sesion, un_consultorio(sesion))

    with pytest.raises(IntegrityError, match="ck_usuario_rol_rol_valido"):
        sesion.execute(
            text("INSERT INTO usuario_rol (usuario_id, rol) VALUES (:usuario_id, 'administrador')"),
            {"usuario_id": usuario.id},
        )
    sesion.rollback()

    with pytest.raises(IntegrityError, match="pk_usuario_rol"):
        for _ in range(2):
            sesion.execute(
                text("INSERT INTO usuario_rol (usuario_id, rol) VALUES (:usuario_id, 'dueno')"),
                {"usuario_id": usuario.id},
            )
    sesion.rollback()


def test_inf1_deshacer_solo_la_migracion_del_horario_deja_el_esquema_de_los_roles(
    engine: Engine, config_alembic: Config, sesion: Session
) -> None:
    consultorio = un_consultorio(sesion)
    un_profesional(sesion, consultorio, horario=(franja(0, "09:00", "13:00"),))
    with engine.connect() as conexion:
        assert conexion.execute(text("SELECT count(*) FROM franja_horaria")).scalar_one() == 1

    command.downgrade(config_alembic, "0007")

    with engine.connect() as conexion:
        assert set(inspect(conexion).get_table_names()) == TABLAS_HASTA_LOS_ROLES | {"alembic_version"}
        assert conexion.execute(text("SELECT count(*) FROM profesional")).scalar_one() == 1

    command.upgrade(config_alembic, "head")

    with engine.connect() as conexion:
        assert set(inspect(conexion).get_table_names()) == TABLAS_DEL_MODELO | {"alembic_version"}
        assert conexion.execute(text("SELECT count(*) FROM franja_horaria")).scalar_one() == 0


def _insertar_franja(sesion: Session, profesional_id: int, **valores) -> None:
    datos = {
        "dia_semana": 0,
        "hora_inicio": time(9, 0),
        "hora_fin": time(13, 0),
        "vigente_desde": None,
        "vigente_hasta": None,
        **valores,
    }
    sesion.execute(
        text(
            "INSERT INTO franja_horaria (profesional_id, dia_semana, hora_inicio, hora_fin, vigente_desde, vigente_hasta) "
            "VALUES (:profesional_id, :dia_semana, :hora_inicio, :hora_fin, :vigente_desde, :vigente_hasta)"
        ),
        {"profesional_id": profesional_id, **datos},
    )


def test_inf1_la_base_rechaza_una_franja_invalida(sesion: Session) -> None:
    from datetime import date

    profesional = un_profesional(sesion, un_consultorio(sesion), horario=())

    for valores, restriccion in (
        ({"hora_inicio": time(13, 0), "hora_fin": time(9, 0)}, "ck_franja_horaria_inicio_antes_del_fin"),
        ({"hora_inicio": time(9, 0), "hora_fin": time(9, 0)}, "ck_franja_horaria_inicio_antes_del_fin"),
        ({"dia_semana": 7}, "ck_franja_horaria_dia_semana"),
        ({"dia_semana": -1}, "ck_franja_horaria_dia_semana"),
        (
            {"vigente_desde": date(2026, 12, 1), "vigente_hasta": date(2026, 11, 1)},
            "ck_franja_horaria_vigencia",
        ),
    ):
        with pytest.raises(IntegrityError, match=restriccion):
            _insertar_franja(sesion, profesional.id, **valores)
        sesion.rollback()

    # La vigencia de un solo día, o con una sola fecha, se guarda.
    _insertar_franja(sesion, profesional.id, vigente_desde=date(2026, 11, 2), vigente_hasta=date(2026, 11, 2))
    _insertar_franja(sesion, profesional.id, dia_semana=1, vigente_desde=date(2026, 11, 2))
    _insertar_franja(sesion, profesional.id, dia_semana=2, vigente_hasta=date(2026, 11, 2))
    sesion.commit()
    assert sesion.execute(text("SELECT count(*) FROM franja_horaria")).scalar_one() == 3
