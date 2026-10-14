"""Errores del recurso que nombra la URL (RN-GL-04, D166): salen como 404, no como 422."""
import pytest

from app.domain.errors import (
    PrestacionNoEncontrada,
    RecursoDeLaUrlNoEncontrado,
    RecursoNoEncontrado,
    ReferenciaInvalida,
    SillonNoEncontrado,
    TurnoNoEncontrado,
)


def test_ca3_sillon_no_encontrado_lleva_rn_gl_04_y_la_referencia() -> None:
    error = SillonNoEncontrado(999)

    assert error.codigos == ["RN-GL-04"]
    assert error.referencias == (ReferenciaInvalida("sillon", 999, "inexistente"),)
    assert error.mensaje == "No existe el sillón 999."


@pytest.mark.parametrize(
    ("clase", "recurso"),
    [
        (TurnoNoEncontrado, "turno"),
        (PrestacionNoEncontrada, "prestacion"),
        (SillonNoEncontrado, "sillon"),
    ],
)
def test_los_tres_no_encontrado_comparten_la_base_y_el_codigo(
    clase: type[RecursoDeLaUrlNoEncontrado], recurso: str
) -> None:
    error = clase(7)

    assert isinstance(error, RecursoDeLaUrlNoEncontrado)
    assert error.codigos == ["RN-GL-04"]
    assert error.referencias == (ReferenciaInvalida(recurso, 7, "inexistente"),)


def test_recurso_no_encontrado_del_cuerpo_no_es_de_la_url() -> None:
    error = RecursoNoEncontrado((ReferenciaInvalida("sillon", 7, "inexistente"),))

    assert not isinstance(error, RecursoDeLaUrlNoEncontrado)
