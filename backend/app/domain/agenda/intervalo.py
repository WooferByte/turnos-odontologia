"""Intervalo semiabierto [inicio, fin) (RN-AG-09)."""
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.domain.errors import IntervaloInvalido
from app.domain.tiempo import exigir_utc


@dataclass(frozen=True)
class Intervalo:
    inicio: datetime
    fin: datetime

    def __post_init__(self) -> None:
        exigir_utc(self.inicio, "inicio")
        exigir_utc(self.fin, "fin")
        if not self.inicio < self.fin:
            raise IntervaloInvalido(
                f"El inicio ({self.inicio.isoformat()}) debe ser anterior al fin "
                f"({self.fin.isoformat()})."
            )

    def se_solapa_con(self, otro: "Intervalo") -> bool:
        """Hay solape si cada uno empieza antes de que termine el otro (RN-AG-09)."""
        return self.inicio < otro.fin and otro.inicio < self.fin

    @classmethod
    def para_turno(cls, inicio: datetime, duracion_minutos: int, zona_horaria: str) -> "Intervalo":
        """Intervalo de un turno nuevo.

        Valida ``inicio`` (RN-GL-01), calcula ``fin`` (RN-AG-02) y exige que el turno
        no cruce la medianoche del consultorio (RN-AG-10d).
        """
        exigir_utc(inicio, "inicio")
        intervalo = cls(inicio, inicio + timedelta(minutes=duracion_minutos))
        zona = ZoneInfo(zona_horaria)
        inicio_local = intervalo.inicio.astimezone(zona)
        fin_local = intervalo.fin.astimezone(zona)
        termina_el_mismo_dia = fin_local.date() == inicio_local.date()
        termina_a_la_medianoche = (
            fin_local.date() == inicio_local.date() + timedelta(days=1)
            and fin_local.time() == time(0, 0)
        )
        if not (termina_el_mismo_dia or termina_a_la_medianoche):
            raise IntervaloInvalido(
                "El turno no puede cruzar la medianoche del consultorio "
                f"({inicio_local:%H:%M} a {fin_local:%H:%M} hora local)."
            )
        return intervalo
