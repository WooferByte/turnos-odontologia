"""Reglas puras de las prestaciones: duración (RN-AG-01) y nombre (RN-AG-15)."""
import pytest

from app.domain.agenda.nombres import clave_de_nombre, normalizar_espacios
from app.domain.agenda.prestaciones import (
    GRANULARIDAD_MINUTOS,
    DatosPrestacion,
    duracion_valida,
    nombre_repetido,
)
from app.domain.errors import DuracionInvalida


def una_prestacion_de_dominio(id: int, nombre: str, activa: bool = True) -> DatosPrestacion:
    return DatosPrestacion(
        id=id,
        consultorio_id=1,
        nombre=nombre,
        duracion_minutos=30,
        color="#9E9E9E",
        reservable_online=False,
        activa=activa,
    )


@pytest.mark.parametrize("minutos", [5, 45, 60])
def test_ca2_duracion_valida_acepta_multiplos_de_5(minutos: int) -> None:
    assert duracion_valida(minutos) is True


@pytest.mark.parametrize("minutos", [47, 0, -5])
def test_ca2_duracion_valida_rechaza_lo_que_no_es_multiplo_o_positivo(minutos: int) -> None:
    assert duracion_valida(minutos) is False


def test_ca1_normalizar_espacios_quita_los_de_mas() -> None:
    assert normalizar_espacios("  Control   de ortodoncia ") == "Control de ortodoncia"


@pytest.mark.parametrize("variante", ["obturacion", " OBTURACIÓN ", "Obturación", "obturacio\u0301n"])
def test_ca1_clave_de_nombre_ignora_mayusculas_acentos_y_espacios(variante: str) -> None:
    assert clave_de_nombre(variante) == clave_de_nombre("Obturación")


def test_ca1_clave_de_nombre_distingue_nombres_distintos() -> None:
    assert clave_de_nombre("Limpieza") != clave_de_nombre("Limpiezas")


def test_ca1_nombre_repetido_encuentra_tambien_las_inactivas() -> None:
    existentes = [
        una_prestacion_de_dominio(1, "Limpieza"),
        una_prestacion_de_dominio(2, "Obturación", activa=False),
    ]

    repetida = nombre_repetido("obturacion", existentes)

    assert repetida is not None
    assert repetida.id == 2
    assert nombre_repetido("Blanqueamiento", existentes) is None


def test_ca1_nombre_repetido_ignora_la_prestacion_que_se_edita() -> None:
    existentes = [una_prestacion_de_dominio(1, "Limpieza"), una_prestacion_de_dominio(2, "Extracción")]

    assert nombre_repetido("limpieza", existentes, excepto_id=1) is None
    otra = nombre_repetido("limpieza", existentes, excepto_id=2)
    assert otra is not None
    assert otra.id == 1


def test_ca2_duracion_invalida_lleva_el_codigo_y_el_campo() -> None:
    error = DuracionInvalida(GRANULARIDAD_MINUTOS)

    assert error.codigos == ["RN-AG-01"]
    assert error.campo == "duracion_minutos"
    assert error.mensaje == "El campo 'duracion_minutos' debe ser mayor que 0 y múltiplo de 5 minutos."
