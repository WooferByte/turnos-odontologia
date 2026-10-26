"""Reglas puras de los usuarios: contraseña inicial (RN-AU-07) y RN-AU-06, sin HTTP ni base (US-093)."""
import pytest

from app.domain.acceso.usuarios import (
    exigir_no_desactivarse,
    exigir_no_restablecer_la_propia,
    exigir_que_quede_un_odontologo,
    validar_contrasena_inicial,
    validar_largo_de_contrasena,
)
from app.domain.errors import (
    AdministracionSinOdontologo,
    ContrasenaActualIncorrecta,
    ContrasenaFueraDeRango,
    EntradaInvalida,
    RestablecerLaPropia,
)


def test_us093_ca9_contrasena_inicial_de_9_caracteres_levanta_contrasena_fuera_de_rango_con_rn_au_07() -> None:
    with pytest.raises(EntradaInvalida) as error:
        validar_contrasena_inicial("corta-123")

    assert error.value.codigos == ["RN-AU-07"]
    assert isinstance(error.value.errores[0], ContrasenaFueraDeRango)
    assert error.value.errores[0].campo == "contrasena"


@pytest.mark.parametrize("contrasena", ["a" * 10, "a" * 72, "á" * 36])
def test_us093_ca9_10_caracteres_y_72_bytes_se_aceptan(contrasena: str) -> None:
    validar_contrasena_inicial(contrasena)


def test_us093_ca9_37_caracteres_con_tilde_que_ocupan_73_bytes_se_rechazan() -> None:
    contrasena = "á" * 36 + "a"
    assert len(contrasena) == 37 and len(contrasena.encode("utf-8")) == 73

    with pytest.raises(EntradaInvalida) as error:
        validar_contrasena_inicial(contrasena)

    assert error.value.codigos == ["RN-AU-07"]


def test_us093_ca9_el_mensaje_del_error_no_repite_la_contrasena() -> None:
    with pytest.raises(EntradaInvalida) as error:
        validar_contrasena_inicial("corta-123")

    assert "corta-123" not in error.value.mensaje
    assert "10 caracteres" in error.value.mensaje and "72 bytes" in error.value.mensaje


def test_us093_ca5_desactivarse_a_si_mismo_levanta_rn_au_06() -> None:
    with pytest.raises(AdministracionSinOdontologo) as error:
        exigir_no_desactivarse(actor_id=1, usuario_id=1, activo_pedido=False)

    assert error.value.codigos == ["RN-AU-06"]
    assert error.value.mensaje == "Nadie puede desactivarse a sí mismo."


def test_us093_ca4_quedarse_sin_odontologos_activos_levanta_rn_au_06() -> None:
    with pytest.raises(AdministracionSinOdontologo) as error:
        exigir_que_quede_un_odontologo(odontologos_activos_despues=0)

    assert error.value.codigos == ["RN-AU-06"]
    assert "odontólogo" in error.value.mensaje


@pytest.mark.parametrize(
    ("actor_id", "usuario_id", "activo_pedido"),
    [(1, 2, False), (1, 1, True), (2, 2, True), (1, 1, None), (1, 2, None)],
)
def test_us093_ca5_desactivar_a_otro_o_reactivarse_no_levanta_nada(
    actor_id: int, usuario_id: int, activo_pedido: bool | None
) -> None:
    exigir_no_desactivarse(actor_id, usuario_id, activo_pedido)


@pytest.mark.parametrize("odontologos_activos_despues", [1, 2])
def test_us093_ca4_con_un_odontologo_activo_despues_del_cambio_no_levanta_nada(
    odontologos_activos_despues: int,
) -> None:
    exigir_que_quede_un_odontologo(odontologos_activos_despues)


def test_us093_ca9_una_contrasena_con_espacios_en_los_extremos_no_se_recorta() -> None:
    validar_contrasena_inicial("a" * 8 + "  ")  # 10 caracteres: recortada serían 8
    validar_contrasena_inicial("  " + "a" * 8)

    with pytest.raises(EntradaInvalida):
        validar_contrasena_inicial("a" * 9)  # 9 caracteres: sigue siendo corta


# --- C-10: una sola regla de largo para la inicial, la restablecida y la cambiada (K3) ---
def test_us093_ca9_una_contrasena_nueva_de_9_caracteres_levanta_contrasena_fuera_de_rango_en_contrasena_nueva() -> None:
    with pytest.raises(EntradaInvalida) as error:
        validar_largo_de_contrasena("corta-123", "contrasena_nueva")

    assert error.value.codigos == ["RN-AU-07"]
    assert isinstance(error.value.errores[0], ContrasenaFueraDeRango)
    assert error.value.errores[0].campo == "contrasena_nueva"


@pytest.mark.parametrize("campo", ["contrasena", "contrasena_nueva"])
@pytest.mark.parametrize("contrasena", ["a" * 10, "a" * 72, "á" * 36])
def test_us093_ca9_10_caracteres_y_72_bytes_se_aceptan_en_los_dos_campos(contrasena: str, campo: str) -> None:
    validar_largo_de_contrasena(contrasena, campo)


@pytest.mark.parametrize("campo", ["contrasena", "contrasena_nueva"])
def test_us093_ca9_37_caracteres_con_tilde_que_ocupan_73_bytes_se_rechazan_en_los_dos_campos(campo: str) -> None:
    contrasena = "á" * 36 + "a"
    assert len(contrasena.encode("utf-8")) == 73

    with pytest.raises(EntradaInvalida) as error:
        validar_largo_de_contrasena(contrasena, campo)

    assert error.value.errores[0].campo == campo  # type: ignore[attr-defined]


def test_us093_ca6_restablecer_la_propia_levanta_restablecer_la_propia_con_rn_au_10() -> None:
    with pytest.raises(RestablecerLaPropia) as error:
        exigir_no_restablecer_la_propia(actor_id=1, usuario_id=1)

    assert error.value.codigos == ["RN-AU-10"]


def test_us093_ca7_la_contrasena_actual_incorrecta_lleva_rn_au_09_y_un_mensaje_fijo_sin_la_contrasena() -> None:
    error = ContrasenaActualIncorrecta()

    assert error.codigos == ["RN-AU-09"]
    assert error.mensaje == "La contraseña actual no es correcta."


def test_us093_ca6_restablecer_a_otro_usuario_no_levanta_nada() -> None:
    exigir_no_restablecer_la_propia(actor_id=1, usuario_id=2)
    exigir_no_restablecer_la_propia(actor_id=2, usuario_id=1)


def test_us093_ca9_la_contrasena_con_espacios_en_los_extremos_no_se_recorta() -> None:
    # 8 caracteres útiles + 2 espacios: cuenta 10, no se recorta (RN-AU-07, D242)
    validar_largo_de_contrasena("  abcdefgh", "contrasena_nueva")
    # 9 caracteres con un espacio al final: sigue siendo corta, pero tampoco se recorta para otra cosa
    with pytest.raises(EntradaInvalida):
        validar_largo_de_contrasena("abcdefgh ", "contrasena_nueva")
    # 71 caracteres + 2 espacios = 73 bytes: se rechaza por bytes, sin recortar
    with pytest.raises(EntradaInvalida):
        validar_largo_de_contrasena("a" * 71 + "  ", "contrasena")


def test_us093_ca9_el_error_del_largo_no_repite_la_contrasena() -> None:
    with pytest.raises(EntradaInvalida) as error:
        validar_largo_de_contrasena("corta-123", "contrasena_nueva")

    assert "corta-123" not in error.value.errores[0].mensaje
    assert "corta-123" not in str(error.value)
