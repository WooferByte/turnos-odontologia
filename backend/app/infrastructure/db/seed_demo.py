"""Seed de la demo de Swagger (D19, D124). Todos los datos son ficticios (RN-PR-01).

Los identificadores se asignan a mano para que sean fijos y el README pueda documentarlos.
Hay un solo profesional y un solo sillón a propósito: así omitirlos funciona (RN-AG-14) y un
segundo turno a la misma hora muestra el ``409`` con los dos códigos (E4).
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.infrastructure.db.modelos import (
    ConsultorioModelo,
    PacienteModelo,
    PrestacionModelo,
    ProfesionalModelo,
    SillonModelo,
)

# Prestaciones y duraciones de 04_modelo_de_datos.md, «Seed data inicial» (D56).
_PRESTACIONES = (
    (1, "Consulta / control", 30),
    (2, "Limpieza", 45),
    (3, "Obturación", 60),
    (4, "Extracción", 45),
    (5, "Urgencia", 30),
)

# Nombres inventados; el bloque 5555-01xx hace de «prefijo de prueba».
_PACIENTES = (
    (1, "Ana", "Ejemplo", "+5491155550101"),
    (2, "Bruno", "Ficticio", "+5491155550102"),
    (3, "Carla", "Inventada", "+5491155550103"),
)


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
    for id_, nombre, duracion in _PRESTACIONES:
        sesion.add(
            PrestacionModelo(
                id=id_, consultorio_id=1, nombre=nombre, duracion_minutos=duracion, activa=True
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


# Tablas con identificador fijo en el seed.
_TABLAS_SEMBRADAS = ("consultorio", "profesional", "sillon", "prestacion", "paciente")


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
