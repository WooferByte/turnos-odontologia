"""Reglas puras de las prestaciones: duración (RN-AG-01) y nombre (RN-AG-15)."""
import pytest

from app.domain.agenda.prestaciones import (
    clave_de_nombre,
    duracion_valida,
    normalizar_espacios,
)


@pytest.mark.parametrize("minutos", [5, 45, 60])
def test_ca2_duracion_valida_acepta_multiplos_de_5(minutos: int) -> None:
    assert duracion_valida(minutos) is True


@pytest.mark.parametrize("minutos", [47, 0, -5])
def test_ca2_duracion_valida_rechaza_lo_que_no_es_multiplo_o_positivo(minutos: int) -> None:
    assert duracion_valida(minutos) is False


def test_ca1_normalizar_espacios_quita_los_de_mas() -> None:
    assert normalizar_espacios("  Control   de ortodoncia ") == "Control de ortodoncia"


@pytest.mark.parametrize("variante", ["obturacion", " OBTURACIÓN ", "Obturación", "obtu\u0072acio\u0301n"])
def test_ca1_clave_de_nombre_ignora_mayusculas_acentos_y_espacios(variante: str) -> None:
    assert clave_de_nombre(variante) == clave_de_nombre("Obturación")
