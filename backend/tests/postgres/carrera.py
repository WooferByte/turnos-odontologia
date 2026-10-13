"""Ayuda para forzar una carrera entre dos reservas del mismo hueco (E11, design I9).

Lanzar dos hilos y esperar que choquen no prueba nada: si uno termina antes de que el otro lea,
el dominio rechaza al segundo y la restricción nunca se ejercita. La carrera se fuerza:

1. el ganador inserta su turno con ``flush()`` y NO confirma;
2. el perdedor corre en otro hilo: el dominio no ve el turno sin confirmar y su ``INSERT``
   queda esperando a la transacción del ganador;
3. se espera, mirando ``pg_stat_activity``, a que alguna sesión esté bloqueada (con tope);
4. el ganador confirma y el perdedor recibe la violación de la restricción.

Ese es el camino de la última defensa (escrituras que no toman el bloqueo de fila). Si el ganador
toma ``bloquear_recursos`` antes de insertar, el perdedor espera en el bloqueo, antes de leer, y
recibe el rechazo del dominio sin llegar a insertar (design I8).
"""
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TypeVar

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.db.modelos import (
    PacienteModelo,
    PrestacionModelo,
    ProfesionalModelo,
    SillonModelo,
    TurnoModelo,
)
from tests.conftest import RELOJ_FIJO
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
)

T = TypeVar("T")

TOPE_DE_ESPERA = 10  # segundos; todas las esperas tienen tope para que un fallo no cuelgue la corrida
BLOQUEADAS = text(
    "SELECT count(*) FROM pg_stat_activity "
    "WHERE datname = current_database() AND wait_event_type = 'Lock' AND pid <> pg_backend_pid()"
)


@dataclass
class Escenario:
    paciente: PacienteModelo
    prestacion: PrestacionModelo  # 30 minutos
    profesional_a: ProfesionalModelo
    profesional_b: ProfesionalModelo
    sillon_1: SillonModelo
    sillon_2: SillonModelo


def crear_escenario(sesion: Session) -> Escenario:
    consultorio = un_consultorio(sesion)
    return Escenario(
        paciente=un_paciente(sesion, consultorio),
        prestacion=una_prestacion(sesion, consultorio),
        profesional_a=un_profesional(sesion, consultorio, nombre="Profesional A"),
        profesional_b=un_profesional(sesion, consultorio, nombre="Profesional B"),
        sillon_1=un_sillon(sesion, consultorio, nombre="Sillón 1"),
        sillon_2=un_sillon(sesion, consultorio, nombre="Sillón 2"),
    )


def turno_sin_confirmar(
    sesion: Session, e: Escenario, profesional: ProfesionalModelo, sillon: SillonModelo, inicio: datetime
) -> int:
    """Inserta el turno ganador con ``flush()``, sin confirmar, y devuelve su id."""
    modelo = TurnoModelo(
        consultorio_id=profesional.consultorio_id,
        paciente_id=e.paciente.id,
        profesional_id=profesional.id,
        sillon_id=sillon.id,
        prestacion_id=e.prestacion.id,
        inicio=inicio,
        fin=inicio + timedelta(minutes=e.prestacion.duracion_minutos),
        duracion_minutos=e.prestacion.duracion_minutos,
        estado="reservado",
        creado_en=RELOJ_FIJO,
    )
    sesion.add(modelo)
    sesion.flush()
    return modelo.id


def esperar_a_que_haya_una_sesion_bloqueada(engine: Engine) -> None:
    limite = time.monotonic() + TOPE_DE_ESPERA
    with engine.connect() as conexion:
        while conexion.execute(BLOQUEADAS).scalar_one() == 0:
            conexion.rollback()  # que la próxima consulta vea el estado nuevo
            if time.monotonic() > limite:
                raise AssertionError(
                    "ninguna sesión quedó esperando un bloqueo: la restricción de exclusión no actúa"
                )
            time.sleep(0.02)


def carrera(
    engine: Engine,
    ganador: Callable[[Session], int],
    perdedor: Callable[[], T],
) -> tuple[int, T]:
    """Corre ``perdedor`` mientras ``ganador`` no confirmó; devuelve (id del ganador, resultado).

    Si ``perdedor`` levanta una excepción, se propaga acá después de que el ganador confirmó.
    """
    fabrica = sessionmaker(bind=engine, expire_on_commit=False)
    with fabrica() as sesion_ganadora, ThreadPoolExecutor(max_workers=1) as hilos:
        id_ganador = ganador(sesion_ganadora)
        futuro = hilos.submit(perdedor)
        try:
            esperar_a_que_haya_una_sesion_bloqueada(engine)
        except AssertionError:
            sesion_ganadora.rollback()  # suelta al perdedor para que el hilo termine
            futuro.exception(timeout=TOPE_DE_ESPERA)
            raise
        sesion_ganadora.commit()
        return id_ganador, futuro.result(timeout=TOPE_DE_ESPERA)


class ReservaGanadora:
    """El ganador de la carrera: guarda su id al insertar, aunque el perdedor levante un error."""

    def __init__(self, e: Escenario, profesional: ProfesionalModelo, sillon: SillonModelo, inicio: datetime):
        self._datos = (e, profesional, sillon, inicio)
        self.id: int | None = None

    def __call__(self, sesion: Session) -> int:
        self.id = turno_sin_confirmar(sesion, *self._datos)
        return self.id


def bloquear_en_otro_hilo(
    engine: Engine, hilos: ThreadPoolExecutor, profesional_id: int, sillon_id: int
):
    """Pide en otra sesión el bloqueo de los recursos y confirma apenas lo obtiene."""
    from app.infrastructure.repositories.agenda import RepositorioAgendaSqlAlchemy

    def tarea() -> None:
        with sessionmaker(bind=engine, expire_on_commit=False)() as sesion:
            RepositorioAgendaSqlAlchemy(sesion).bloquear_recursos(profesional_id, sillon_id)
            sesion.commit()

    return hilos.submit(tarea)
