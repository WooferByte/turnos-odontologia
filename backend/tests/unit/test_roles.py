"""Roles y permisos del panel: la matriz de design R4, sin HTTP ni base (US-091, RN-AU-02, RN-AU-05)."""
import pytest

from app.domain.acceso.roles import MATRIZ, Permiso, Rol, exigir_permiso, puede
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
    ("usuarios.leer", True, False, True),
    ("usuarios.editar", True, False, False),
    ("horario.leer", True, True, True),
    ("horario.editar", True, False, False),
    ("profesionales.leer", True, True, True),
]
CASOS_MATRIZ = [
    (permiso, rol, esperado)
    for permiso, od, rec, due in TABLA_R4
    for rol, esperado in ((ODONTOLOGO, od), (RECEPCIONISTA, rec), (DUENO, due))
]


@pytest.mark.parametrize(("permiso", "rol", "esperado"), CASOS_MATRIZ)
def test_us091_ca3_matriz_de_las_rutas_existentes(permiso, rol, esperado):
    assert puede(frozenset({rol}), Permiso(permiso)) is esperado


def test_us091_ca3_la_tabla_cubre_los_11_permisos_y_los_3_roles():
    assert {Permiso(p) for p, *_ in TABLA_R4} == set(Permiso)
    assert len(CASOS_MATRIZ) == 11 * 3


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


@pytest.mark.parametrize("permiso", list(Permiso))
def test_us091_ca3_cada_permiso_tiene_al_menos_un_rol(permiso):
    assert MATRIZ[permiso]
    assert MATRIZ[permiso] <= set(Rol)


def test_us091_ca3_la_matriz_tiene_un_renglon_por_permiso():
    assert set(MATRIZ) == set(Permiso)


def test_us091_ca1_rol_desconocido_no_existe():
    with pytest.raises(ValueError):
        Rol("administrador")


def test_us093_ca1_usuarios_leer_para_odontologo_y_dueno_usuarios_editar_solo_para_odontologo() -> None:
    assert MATRIZ[Permiso.USUARIOS_LEER] == {ODONTOLOGO, DUENO}
    assert MATRIZ[Permiso.USUARIOS_EDITAR] == {ODONTOLOGO}
    assert not puede(frozenset({RECEPCIONISTA}), Permiso.USUARIOS_LEER)


def test_us002_ca1_horario_leer_y_profesionales_leer_para_los_tres_roles_y_horario_editar_solo_odontologo():
    for rol in (ODONTOLOGO, RECEPCIONISTA, DUENO):
        assert puede(frozenset({rol}), Permiso.HORARIO_LEER)
        assert puede(frozenset({rol}), Permiso.PROFESIONALES_LEER)
    assert puede(frozenset({ODONTOLOGO}), Permiso.HORARIO_EDITAR)
    assert not puede(frozenset({RECEPCIONISTA}), Permiso.HORARIO_EDITAR)
    assert not puede(frozenset({DUENO}), Permiso.HORARIO_EDITAR)
