"""Seed de la demo de Swagger (D19, D124). Todos los datos son ficticios (RN-PR-01).

Los identificadores se asignan a mano para que sean fijos y el README pueda documentarlos.
Hay un solo profesional y un solo sillón a propósito: así omitirlos funciona (RN-AG-14) y un
segundo turno a la misma hora muestra el ``409`` con los dos códigos (E4).
"""
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.infrastructure.db.modelos import (
    ConsultorioModelo,
    PacienteModelo,
    PrestacionModelo,
    ProfesionalModelo,
    SillonModelo,
    UsuarioModelo,
)
from app.domain.tiempo import utc_now

# Prestaciones y duraciones de 04_modelo_de_datos.md, «Seed data inicial» (D56).
_PRESTACIONES = (
    (1, "Consulta / control", 30, "#1E88E5"),
    (2, "Limpieza", 45, "#43A047"),
    (3, "Obturación", 60, "#FB8C00"),
    (4, "Extracción", 45, "#E53935"),
    (5, "Urgencia", 30, "#8E24AA"),
)

# Nombres inventados; el bloque 5555-01xx hace de «prefijo de prueba».
_PACIENTES = (
    (1, "Ana", "Ejemplo", "+5491155550101"),
    (2, "Bruno", "Ficticio", "+5491155550102"),
    (3, "Carla", "Inventada", "+5491155550103"),
)

# Usuario ficticio del panel (design J11, D197, D202): sin roles hasta C-07. La contraseña es
# solo de la demo en memoria; en PostgreSQL la define SEED_USUARIO_PASSWORD.
EMAIL_DEMO = "odontologa@consultorio-demo.test"
CONTRASENA_DEMO = "demo-consultorio-2026"


def cargar_demo(sesion: Session) -> None:
    """Carga el consultorio de demo y confirma. Se espera una base recién creada y vacía."""
    sesion.add(
        ConsultorioModelo(
            id=1,
            nombre="Consultorio Demo",
            slug="consultorio-demo",
            zona_horaria="America/Argentina/Buenos_Aires",
        )
    )
    sesion.add(ProfesionalModelo(id=1, consultorio_id=1, nombre="Dra. Demo Ficticia", activo=True))
    sesion.add(SillonModelo(id=1, consultorio_id=1, nombre="Sillón 1", activo=True))
    for id_, nombre, duracion, color in _PRESTACIONES:
        sesion.add(
            PrestacionModelo(
                id=id_,
                consultorio_id=1,
                nombre=nombre,
                duracion_minutos=duracion,
                color=color,
                reservable_online=False,
                activa=True,
            )
        )
    for id_, nombre, apellido, telefono in _PACIENTES:
        sesion.add(
            PacienteModelo(
                id=id_,
                consultorio_id=1,
                nombre=nombre,
                apellido=apellido,
                telefono_whatsapp=telefono,
            )
        )
    sesion.commit()


def cargar_demo_si_falta(sesion: Session) -> bool:
    """Carga la demo solo si el consultorio 1 no existe; devuelve si cargó (design I13).

    Permite repetir el arranque del contenedor sin duplicar datos ni fallar.
    """
    if sesion.get(ConsultorioModelo, 1) is not None:
        return False
    cargar_demo(sesion)
    return True


def cargar_usuario_demo(sesion: Session, hash_password: str) -> None:
    """Carga el usuario del seed (id 1, consultorio 1) con el hash ya calculado y confirma."""
    sesion.add(
        UsuarioModelo(
            id=1,
            consultorio_id=1,
            email=EMAIL_DEMO,
            hash_password=hash_password,
            activo=True,
            token_version=0,
            creado_en=utc_now(),
        )
    )
    sesion.commit()


def cargar_usuario_demo_si_falta(sesion: Session, hash_password: str) -> bool:
    """Carga el usuario solo si no hay uno con ese email; devuelve si cargó (design J11).

    Va aparte de ``cargar_demo_si_falta``: un volumen sembrado antes de C-06 ya tiene el
    consultorio 1 y aun así tiene que recibir el usuario.
    """
    if sesion.scalar(select(UsuarioModelo.id).where(UsuarioModelo.email == EMAIL_DEMO)) is not None:
        return False
    cargar_usuario_demo(sesion, hash_password)
    return True


# Tablas con identificador fijo en el seed.
_TABLAS_SEMBRADAS = ("consultorio", "profesional", "sillon", "prestacion", "paciente", "usuario")


def ajustar_secuencias(sesion: Session) -> None:
    """Avanza la secuencia de ``id`` de cada tabla sembrada hasta su máximo (design I13).

    El seed asigna los identificadores a mano y en PostgreSQL eso no mueve la secuencia: el
    primer alta sin identificador explícito chocaría con el 1. En SQLite no hace falta.
    """
    if sesion.get_bind().dialect.name != "postgresql":
        return
    for tabla in _TABLAS_SEMBRADAS:
        sesion.execute(
            text(
                f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), "
                f"(SELECT max(id) FROM {tabla}))"
            )
        )
    sesion.commit()
