"""Horario recurrente del profesional: franjas válidas (RN-AG-16) y turno dentro de una franja (RN-AG-04).

Solo biblioteca estándar (regla dura 3). Las horas de una franja son del consultorio, intervalo
semiabierto ``[hora_inicio, hora_fin)``; ``dia_semana`` va de 0 (lunes) a 6 (domingo).
"""
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, time
from zoneinfo import ZoneInfo

from app.domain.agenda.intervalo import Intervalo
from app.domain.errors import FranjaInvalida, FueraDeHorario


@dataclass(frozen=True)
class Franja:
    dia_semana: int
    hora_inicio: time
    hora_fin: time
    vigente_desde: date | None = None
    vigente_hasta: date | None = None

    def vigente_el(self, dia: date) -> bool:
        """Sin límite (``None``) siempre vigente; cada límite incluye su fecha (D259)."""
        return (self.vigente_desde is None or self.vigente_desde <= dia) and (
            self.vigente_hasta is None or dia <= self.vigente_hasta
        )


def _se_superponen(a: Franja, b: Franja) -> bool:
    """Intervalos semiabiertos del mismo día: las contiguas no se superponen (RN-AG-09)."""
    return a.hora_inicio < b.hora_fin and b.hora_inicio < a.hora_fin


def validar_franjas(franjas: Sequence[Franja]) -> tuple[FranjaInvalida, ...]:
    """Errores de RN-AG-16 en el orden del cuerpo (D257, D266).

    Una franja invertida o de duración cero se informa y no se compara con las demás. Una válida
    (es decir, no invertida) que se superpone con alguna anterior válida del mismo día se informa;
    la anterior cuenta aunque ya se haya informado.
    """
    errores: list[FranjaInvalida] = []
    validas: list[Franja] = []
    for posicion, franja in enumerate(franjas):
        if franja.hora_inicio >= franja.hora_fin:
            errores.append(FranjaInvalida(posicion, "invertida"))
            continue
        if any(a.dia_semana == franja.dia_semana and _se_superponen(a, franja) for a in validas):
            errores.append(FranjaInvalida(posicion, "superpuesta"))
        validas.append(franja)
    return tuple(errores)


def exigir_dentro_del_horario(intervalo: Intervalo, franjas: Sequence[Franja], zona_horaria: str) -> None:
    """El turno debe caber entero en UNA franja vigente del día del consultorio (RN-AG-04, D256, D258).

    El día es el de ``inicio`` en la zona del consultorio, no el de UTC (RN-GL-01). Si ``fin`` cae
    en otra fecha local (a las 00:00 del día siguiente), ninguna franja lo contiene (D265).
    """
    zona = ZoneInfo(zona_horaria)
    inicio = intervalo.inicio.astimezone(zona)
    fin = intervalo.fin.astimezone(zona)
    if fin.date() == inicio.date():
        for franja in franjas:
            if (
                franja.dia_semana == inicio.weekday()
                and franja.vigente_el(inicio.date())
                and franja.hora_inicio <= inicio.time()
                and fin.time() <= franja.hora_fin
            ):
                return
    raise FueraDeHorario()
