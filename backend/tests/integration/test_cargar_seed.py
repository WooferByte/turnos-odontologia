"""``cargar_seed`` valida ``SEED_USUARIO_PASSWORD`` antes de abrir la base (design J11, RN-AU-07)."""
import pytest

from app.infrastructure.configuracion import ConfiguracionInvalida
from app.infrastructure.db import cargar_seed

URL_DE_PRUEBA = "sqlite+pysqlite:///:memory:"


@pytest.fixture
def motores_abiertos(monkeypatch) -> list[str]:
    abiertos: list[str] = []
    original = cargar_seed.crear_engine

    def registrar(url: str):
        abiertos.append(url)
        return original(url)

    monkeypatch.setattr(cargar_seed, "crear_engine", registrar)
    return abiertos


@pytest.mark.parametrize(
    "contrasena",
    [
        pytest.param(None, id="ausente"),
        pytest.param("", id="vacia"),
        pytest.param("a" * 9, id="9-caracteres"),
        pytest.param("a" * 73, id="73-bytes"),
        pytest.param("ñ" * 37, id="74-bytes-con-tildes"),
    ],
)
def test_cargar_seed_con_contrasena_invalida_falla_antes_de_abrir_la_base(
    contrasena, motores_abiertos
):
    entorno = {"DATABASE_URL": URL_DE_PRUEBA}
    if contrasena is not None:
        entorno["SEED_USUARIO_PASSWORD"] = contrasena

    with pytest.raises(ConfiguracionInvalida, match="SEED_USUARIO_PASSWORD") as error:
        cargar_seed.main(entorno)

    assert motores_abiertos == []
    if contrasena:
        assert contrasena not in str(error.value)
