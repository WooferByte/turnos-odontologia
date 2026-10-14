"""Errores del recurso que nombra la URL (RN-GL-04, D166): salen como 404, no como 422."""
from app.domain.errors import ReferenciaInvalida, SillonNoEncontrado


def test_ca3_sillon_no_encontrado_lleva_rn_gl_04_y_la_referencia() -> None:
    error = SillonNoEncontrado(999)

    assert error.codigos == ["RN-GL-04"]
    assert error.referencias == (ReferenciaInvalida("sillon", 999, "inexistente"),)
    assert error.mensaje == "No existe el sillón 999."
