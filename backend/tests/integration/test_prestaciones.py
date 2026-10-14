"""Casos de uso de prestaciones sobre SQLite en memoria (US-001 CA-1; RN-AG-15, RN-GL-04)."""
import pytest

from app.application.prestaciones import (
    CrearPrestacionComando,
    EditarPrestacionComando,
    crear_prestacion,
    editar_prestacion,
    listar_prestaciones,
)
from app.domain.errors import (
    DuracionInvalida,
    EntradaInvalida,
    NombreDePrestacionRepetido,
    PrestacionNoEncontrada,
)
from app.infrastructure.db.modelos import TurnoModelo
from tests.conftest import a_las
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
)


def _alta(nombre: str = "Blanqueamiento", **kw) -> CrearPrestacionComando:
    datos = {"nombre": nombre, "duracion_minutos": 60, "color": "#3A7BD5"}
    return CrearPrestacionComando(**{**datos, **kw})


def test_ca1_crear_prestacion_la_guarda_activa_y_no_reservable(sesion, uow) -> None:
    un_consultorio(sesion)

    creada = crear_prestacion(_alta(), uow)

    assert creada.id is not None
    assert (creada.nombre, creada.duracion_minutos, creada.color) == ("Blanqueamiento", 60, "#3A7BD5")
    assert creada.activa is True
    assert creada.reservable_online is False
    assert listar_prestaciones(uow) == [creada]  # confirmada: otra sesión la ve


def test_ca1_listar_prestaciones_incluye_las_inactivas(sesion, uow) -> None:
    consultorio = un_consultorio(sesion)
    activa = una_prestacion(sesion, consultorio, nombre="Limpieza")
    inactiva = una_prestacion(sesion, consultorio, nombre="Obturación", activa=False)

    listadas = listar_prestaciones(uow)

    assert [(p.id, p.nombre, p.activa) for p in listadas] == [
        (activa.id, "Limpieza", True),
        (inactiva.id, "Obturación", False),
    ]


def test_ca1_nombre_repetido_rechaza_con_rn_ag_15(sesion, uow) -> None:
    consultorio = un_consultorio(sesion)
    una_prestacion(sesion, consultorio, nombre="Limpieza")

    with pytest.raises(NombreDePrestacionRepetido) as excinfo:
        crear_prestacion(_alta("Limpieza"), uow)

    assert excinfo.value.codigos == ["RN-AG-15"]
    assert [p.nombre for p in listar_prestaciones(uow)] == ["Limpieza"]


def test_ca1_nombre_repetido_sin_mayusculas_ni_acentos_y_entre_inactivas(sesion, uow) -> None:
    consultorio = un_consultorio(sesion)
    una_prestacion(sesion, consultorio, nombre="Obturación", activa=False)

    with pytest.raises(NombreDePrestacionRepetido) as excinfo:
        crear_prestacion(_alta("obturacion"), uow)

    assert excinfo.value.codigos == ["RN-AG-15"]
    assert excinfo.value.nombre_existente == "Obturación"
    assert [p.nombre for p in listar_prestaciones(uow)] == ["Obturación"]


def test_ca1_editar_cambia_solo_los_campos_pedidos(sesion, uow) -> None:
    consultorio = un_consultorio(sesion)
    original = una_prestacion(sesion, consultorio, nombre="Limpieza", duracion_minutos=45)

    editada = editar_prestacion(original.id, EditarPrestacionComando(color="#43A047"), uow)

    assert editada.color == "#43A047"
    assert (editada.nombre, editada.duracion_minutos, editada.reservable_online, editada.activa) == (
        "Limpieza",
        45,
        False,
        True,
    )
    assert listar_prestaciones(uow) == [editada]


@pytest.mark.parametrize("nombre_nuevo", ["Limpieza", "LIMPIEZA"])
def test_ca1_renombrar_con_el_nombre_de_otra_rechaza_y_no_cambia_nada(
    sesion, uow, nombre_nuevo: str
) -> None:
    consultorio = un_consultorio(sesion)
    una_prestacion(sesion, consultorio, nombre="Limpieza")
    a_renombrar = una_prestacion(sesion, consultorio, nombre="Obturación")
    antes = listar_prestaciones(uow)

    with pytest.raises(NombreDePrestacionRepetido) as excinfo:
        editar_prestacion(a_renombrar.id, EditarPrestacionComando(nombre=nombre_nuevo), uow)

    assert excinfo.value.codigos == ["RN-AG-15"]
    assert listar_prestaciones(uow) == antes


@pytest.mark.parametrize("nombre_nuevo", ["Extracción", "extracción"])
def test_ca1_renombrar_con_su_propio_nombre_se_acepta(sesion, uow, nombre_nuevo: str) -> None:
    consultorio = un_consultorio(sesion)
    propia = una_prestacion(sesion, consultorio, nombre="Extracción")

    editada = editar_prestacion(propia.id, EditarPrestacionComando(nombre=nombre_nuevo), uow)

    assert editada.nombre == nombre_nuevo


def test_ca1_desactivar_y_reactivar(sesion, uow) -> None:
    consultorio = un_consultorio(sesion)
    prestacion = una_prestacion(sesion, consultorio)

    desactivada = editar_prestacion(prestacion.id, EditarPrestacionComando(activa=False), uow)
    assert desactivada.activa is False
    assert [p.activa for p in listar_prestaciones(uow)] == [False]  # sigue listada

    reactivada = editar_prestacion(prestacion.id, EditarPrestacionComando(activa=True), uow)
    assert reactivada.activa is True


def test_ca1_editar_prestacion_inexistente_rechaza_con_rn_gl_04(sesion, uow) -> None:
    un_consultorio(sesion)

    with pytest.raises(PrestacionNoEncontrada) as excinfo:
        editar_prestacion(999, EditarPrestacionComando(color="#43A047"), uow)

    assert excinfo.value.codigos == ["RN-GL-04"]
    (referencia,) = excinfo.value.referencias
    assert (referencia.recurso, referencia.recurso_id, referencia.motivo) == (
        "prestacion",
        999,
        "inexistente",
    )


@pytest.mark.parametrize("duracion", [47, 0, -5])
def test_ca2_crear_con_duracion_invalida_rechaza_con_rn_ag_01(sesion, uow, duracion: int) -> None:
    un_consultorio(sesion)

    with pytest.raises(EntradaInvalida) as excinfo:
        crear_prestacion(_alta(duracion_minutos=duracion), uow)

    assert excinfo.value.codigos == ["RN-AG-01"]
    (error,) = excinfo.value.errores
    assert isinstance(error, DuracionInvalida)
    assert error.campo == "duracion_minutos"
    assert listar_prestaciones(uow) == []


def test_ca2_editar_con_duracion_invalida_rechaza_y_no_cambia(sesion, uow) -> None:
    consultorio = un_consultorio(sesion)
    prestacion = una_prestacion(sesion, consultorio, duracion_minutos=30)

    aceptada = editar_prestacion(prestacion.id, EditarPrestacionComando(duracion_minutos=50), uow)
    assert aceptada.duracion_minutos == 50

    with pytest.raises(EntradaInvalida) as excinfo:
        editar_prestacion(prestacion.id, EditarPrestacionComando(duracion_minutos=52), uow)

    assert excinfo.value.codigos == ["RN-AG-01"]
    assert [p.duracion_minutos for p in listar_prestaciones(uow)] == [50]


def test_ca2_la_duracion_invalida_se_informa_antes_que_el_nombre_repetido(sesion, uow) -> None:
    consultorio = un_consultorio(sesion)
    una_prestacion(sesion, consultorio, nombre="Limpieza")

    with pytest.raises(EntradaInvalida) as excinfo:
        crear_prestacion(_alta("Limpieza", duracion_minutos=47), uow)

    assert excinfo.value.codigos == ["RN-AG-01"]


def test_ca2_cinco_minutos_es_el_minimo_aceptado(sesion, uow) -> None:
    un_consultorio(sesion)

    creada = crear_prestacion(_alta(duracion_minutos=5), uow)
    editada = editar_prestacion(creada.id, EditarPrestacionComando(duracion_minutos=5), uow)

    assert (creada.duracion_minutos, editada.duracion_minutos) == (5, 5)


def test_ca3_editar_la_prestacion_no_modifica_la_fila_del_turno(sesion, uow, fabrica_sesiones) -> None:
    consultorio = un_consultorio(sesion)
    prestacion = una_prestacion(sesion, consultorio, duracion_minutos=30)
    turno = un_turno(
        sesion,
        paciente=un_paciente(sesion, consultorio),
        profesional=un_profesional(sesion, consultorio),
        sillon=un_sillon(sesion, consultorio),
        prestacion=prestacion,
        inicio=a_las(10),
    )

    editar_prestacion(prestacion.id, EditarPrestacionComando(duracion_minutos=60, activa=False), uow)

    with fabrica_sesiones() as otra:
        guardado = otra.get(TurnoModelo, turno.id)
        assert (guardado.inicio, guardado.fin, guardado.duracion_minutos) == (
            a_las(10),
            a_las(10, 30),
            30,
        )
