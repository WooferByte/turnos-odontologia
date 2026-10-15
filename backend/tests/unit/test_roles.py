"""Roles y permisos del panel: la matriz de design R4, sin HTTP ni base (US-091, RN-AU-02, RN-AU-05)."""
import pytest

from app.domain.acceso.roles import Permiso, Rol, exigir_permiso, puede
from app.domain.errors import PermisoInsuficiente

ODONTOLOGO, RECEPCIONISTA, DUENO = Rol.ODONTOLOGO, Rol.RECEPCIONISTA, Rol.DUENO

# Renglón a renglón igual que la tabla de design R4: (permiso, odontólogo, recepcionista, dueño).
TABLA_R4 = [
    ("turnos.crear", True, True, False),
    ("historial.leer", True, True, True),
    ("prestaciones.leer", True, True, True),
    ("prestaciones.editar", True, False, False),
    ("sillones.leer", True, True, True),
    ("sillones.editar", True, False, False),
]
CASOS_MATRIZ = [
    (permiso, rol, esperado)
    for permiso, od, rec, due in TABLA_R4
    for rol, esperado in ((ODONTOLOGO, od), (RECEPCIONISTA, rec), (DUENO, due))
]


@pytest.mark.parametrize(("permiso", "rol", "esperado"), CASOS_MATRIZ)
def test_us091_ca3_matriz_de_las_rutas_existentes(permiso, rol, esperado):
    assert puede(frozenset({rol}), Permiso(permiso)) is esperado


def test_us091_ca3_la_tabla_cubre_los_6_permisos_y_los_3_roles():
    assert {Permiso(p) for p, *_ in TABLA_R4} == set(Permiso)
    assert len(CASOS_MATRIZ) == 6 * 3


def test_us091_ca1_los_permisos_son_la_union_de_los_roles():
    recepcion_y_dueno = frozenset({RECEPCIONISTA, DUENO})
    odontologa_y_dueno = frozenset({ODONTOLOGO, DUENO})

    assert puede(recepcion_y_dueno, Permiso.TURNOS_CREAR)
    assert puede(recepcion_y_dueno, Permiso.HISTORIAL_LEER)
    assert not puede(recepcion_y_dueno, Permiso.PRESTACIONES_EDITAR)
    assert all(puede(odontologa_y_dueno, permiso) for permiso in Permiso)


def test_us091_ca3_sin_roles_no_hay_ningun_permiso():
    assert not any(puede(frozenset(), permiso) for permiso in Permiso)


def test_us091_ca3_exigir_permiso_levanta_rn_au_05():
    with pytest.raises(PermisoInsuficiente) as error:
        exigir_permiso(frozenset({DUENO}), Permiso.TURNOS_CREAR)

    assert error.value.codigos == ["RN-AU-05"]
    assert error.value.mensaje == "Tu usuario no tiene permiso para esta operación."


def test_us091_ca3_exigir_permiso_no_levanta_nada_si_algun_rol_alcanza():
    exigir_permiso(frozenset({DUENO, RECEPCIONISTA}), Permiso.TURNOS_CREAR)
