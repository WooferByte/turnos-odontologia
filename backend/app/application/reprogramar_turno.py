"""Caso de uso: reprogramar un turno (C-16; US-012, DD-05). No hace ``commit()`` ni arma SQL."""
from dataclasses import dataclass
from datetime import datetime

from app.application.crear_turno import INTENTOS_ANTE_CARRERA, evaluar_horario_de_un_turno
from app.application.puertos import SolapamientoEnLaBase, UnidadDeTrabajo
from app.application.turno_propio import turno_propio_para_cambiar
from app.domain.errors import (
    DuracionInvalida,
    EntradaInvalida,
    ErrorDeDominio,
    FechaNoUTC,
)
from app.domain.tiempo import Reloj, exigir_utc, utc_now
from app.domain.turnos.eventos import Actor, evento_reprogramado
from app.domain.turnos.reprogramacion import exigir_duracion_del_turno, exigir_reprogramable
from app.domain.turnos.turno import Turno


@dataclass(frozen=True)
class ReprogramarTurnoComando:
    """Un campo en ``None`` significa «no cambia»: el ``null`` explícito ya lo rechazó la API (M2)."""

    turno_id: int
    inicio: datetime | None = None
    duracion_minutos: int | None = None


def _validar_entrada(comando: ReprogramarTurnoComando) -> None:
    """RN-GL-01 y RN-AG-01 juntas en un único ``EntradaInvalida`` (RN-GL-02, D135)."""
    errores: list[ErrorDeDominio] = []
    if comando.inicio is not None:
        try:
            exigir_utc(comando.inicio, "inicio")
        except FechaNoUTC as error:
            errores.append(error)
    if comando.duracion_minutos is not None:
        try:
            exigir_duracion_del_turno(comando.duracion_minutos)
        except DuracionInvalida as error:
            errores.append(error)
    if errores:
        raise EntradaInvalida(tuple(errores))


def _intentar_reprogramar(
    comando: ReprogramarTurnoComando, usuario_id: int, uow: UnidadDeTrabajo, reloj: Reloj, actor: Actor
) -> Turno:
    with uow:
        turno = turno_propio_para_cambiar(uow, usuario_id, comando.turno_id)
        _validar_entrada(comando)
        inicio = turno.inicio if comando.inicio is None else comando.inicio
        duracion = turno.duracion_minutos if comando.duracion_minutos is None else comando.duracion_minutos
        if inicio == turno.inicio and duracion == turno.duracion_minutos:
            return turno  # sin cambios: ni reglas ni evento (D333)
        exigir_reprogramable(turno.estado)
        intervalo = evaluar_horario_de_un_turno(
            uow,
            consultorio_id=turno.consultorio_id,
            profesional_id=turno.profesional_id,
            sillon_id=turno.sillon_id,
            inicio=inicio,
            duracion_minutos=duracion,
            excluir_turno_id=turno.id,
        )
        guardado = uow.agenda.reprogramar(turno.id, intervalo.inicio, intervalo.fin, duracion)
        uow.historial.registrar(evento_reprogramado(turno, guardado, actor, reloj()))
        return guardado


def reprogramar_turno(
    comando: ReprogramarTurnoComando,
    usuario_id: int,
    uow: UnidadDeTrabajo,
    reloj: Reloj = utc_now,
    *,
    actor: Actor,
) -> Turno:
    """Mueve el turno o le cambia la duración; ante una carrera (E11) reevalúa como el alta (M6)."""
    for _ in range(INTENTOS_ANTE_CARRERA - 1):
        try:
            return _intentar_reprogramar(comando, usuario_id, uow, reloj, actor)
        except SolapamientoEnLaBase:
            continue
    return _intentar_reprogramar(comando, usuario_id, uow, reloj, actor)
