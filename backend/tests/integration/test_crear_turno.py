"""Caso de uso ``crear_turno`` con repositorio real sobre SQLite en memoria (D12, D16)."""
from dataclasses import replace
from datetime import datetime

import pytest
from sqlalchemy import select

from app.application.crear_turno import CrearTurnoComando, crear_turno
from app.domain.errors import (
    Conflicto,
    EntradaInvalida,
    ErrorDeSolapamiento,
    IntervaloInvalido,
    ReferenciaInvalida,
)
from app.domain.tiempo import UTC
from app.domain.turnos.estados import EstadoTurno
from app.infrastructure.db.modelos import TurnoModelo
from tests.conftest import RELOJ_FIJO, a_las, reloj_fijo
from tests.factories import (
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
)



def _escenario(sesion, duracion_minutos: int = 30) -> dict:
    consultorio = un_consultorio(sesion)
    return {
        "consultorio": consultorio,
        "paciente": un_paciente(sesion, consultorio),
        "profesional": un_profesional(sesion, consultorio),
        "sillon": un_sillon(sesion, consultorio),
        "prestacion": una_prestacion(sesion, consultorio, duracion_minutos=duracion_minutos),
    }


def _comando(datos: dict, inicio: datetime) -> CrearTurnoComando:
    return CrearTurnoComando(
        paciente_id=datos["paciente"].id,
        prestacion_id=datos["prestacion"].id,
        inicio=inicio,
        profesional_id=datos["profesional"].id,
        sillon_id=datos["sillon"].id,
    )


def test_e1_feliz_crea_turno_reservado_con_fin_calculado(sesion, fabrica_sesiones, uow):
    datos = _escenario(sesion, duracion_minutos=30)

    turno = crear_turno(_comando(datos, a_las(10)), uow, reloj_fijo)

    assert turno.id is not None
    assert turno.estado == EstadoTurno.RESERVADO
    assert turno.inicio == a_las(10)
    assert turno.fin == a_las(10, 30)
    assert turno.duracion_minutos == 30
    assert turno.consultorio_id == datos["profesional"].consultorio_id
    assert turno.creado_en == RELOJ_FIJO
    with fabrica_sesiones() as otra_sesion:  # sesión nueva: lo que quedó confirmado en la base
        guardado = otra_sesion.get(TurnoModelo, turno.id)
    assert guardado is not None
    assert guardado.estado == "reservado"
    assert guardado.inicio == a_las(10)
    assert guardado.fin == a_las(10, 30)
    assert guardado.consultorio_id == datos["consultorio"].id
    assert guardado.profesional_id == datos["profesional"].id
    assert guardado.sillon_id == datos["sillon"].id
    assert guardado.creado_en == RELOJ_FIJO


@pytest.mark.parametrize(
    ("duracion_minutos", "fin_esperado"),
    [(30, a_las(10, 30)), (45, a_las(10, 45)), (60, a_las(11))],
)
def test_e1_fin_es_inicio_mas_la_duracion_de_la_prestacion(
    sesion, fabrica_sesiones, uow, duracion_minutos, fin_esperado
):
    datos = _escenario(sesion, duracion_minutos=duracion_minutos)

    turno = crear_turno(_comando(datos, a_las(10)), uow, reloj_fijo)

    assert turno.fin == fin_esperado
    assert turno.duracion_minutos == duracion_minutos
    with fabrica_sesiones() as otra_sesion:
        assert otra_sesion.get(TurnoModelo, turno.id).fin == fin_esperado


def test_e1_si_el_caso_de_uso_falla_no_queda_ningun_turno(sesion, fabrica_sesiones, uow):
    datos = _escenario(sesion, duracion_minutos=30)
    cruza_la_medianoche = datetime(2026, 11, 3, 2, 45, tzinfo=UTC)  # 23:45 a 00:15 en Buenos Aires

    with pytest.raises(IntervaloInvalido):
        crear_turno(_comando(datos, cruza_la_medianoche), uow, reloj_fijo)

    with fabrica_sesiones() as otra_sesion:
        assert otra_sesion.scalars(select(TurnoModelo)).all() == []


@pytest.mark.parametrize(
    ("hora", "minuto", "duracion_minutos"),
    [
        pytest.param(10, 15, 30, id="solape-parcial"),
        pytest.param(10, 0, 30, id="identico"),
        pytest.param(10, 10, 15, id="contenido"),
        pytest.param(9, 45, 60, id="contiene-al-existente"),
    ],
)
def test_e2_profesional_ocupado_rechaza_con_rn_ag_05(
    sesion, fabrica_sesiones, uow, hora, minuto, duracion_minutos
):
    datos = _escenario(sesion, duracion_minutos=30)
    prestacion_pedida = una_prestacion(
        sesion, datos["consultorio"], duracion_minutos=duracion_minutos
    )
    sillon_2 = un_sillon(sesion, datos["consultorio"])
    existente = un_turno(
        sesion,
        paciente=datos["paciente"],
        profesional=datos["profesional"],
        sillon=datos["sillon"],
        prestacion=datos["prestacion"],
        inicio=a_las(10),
    )
    comando = CrearTurnoComando(
        paciente_id=datos["paciente"].id,
        prestacion_id=prestacion_pedida.id,
        inicio=a_las(hora, minuto),
        profesional_id=datos["profesional"].id,
        sillon_id=sillon_2.id,
    )

    with pytest.raises(ErrorDeSolapamiento) as excinfo:
        crear_turno(comando, uow, reloj_fijo)

    assert excinfo.value.codigos == ["RN-AG-05"]
    assert excinfo.value.conflictos == (
        Conflicto(
            codigo="RN-AG-05",
            recurso="profesional",
            recurso_id=datos["profesional"].id,
            turno_id=existente.id,
        ),
    )
    with fabrica_sesiones() as otra_sesion:
        assert len(otra_sesion.scalars(select(TurnoModelo)).all()) == 1  # solo el existente


def test_e3_sillon_ocupado_rechaza_con_rn_ag_08(sesion, fabrica_sesiones, uow):
    datos = _escenario(sesion, duracion_minutos=30)
    profesional_b = un_profesional(sesion, datos["consultorio"])
    existente = un_turno(
        sesion,
        paciente=datos["paciente"],
        profesional=datos["profesional"],
        sillon=datos["sillon"],
        prestacion=datos["prestacion"],
        inicio=a_las(10),
    )
    comando = CrearTurnoComando(
        paciente_id=datos["paciente"].id,
        prestacion_id=datos["prestacion"].id,
        inicio=a_las(10),
        profesional_id=profesional_b.id,
        sillon_id=datos["sillon"].id,
    )

    with pytest.raises(ErrorDeSolapamiento) as excinfo:
        crear_turno(comando, uow, reloj_fijo)

    assert excinfo.value.codigos == ["RN-AG-08"]
    assert excinfo.value.conflictos == (
        Conflicto(
            codigo="RN-AG-08",
            recurso="sillon",
            recurso_id=datos["sillon"].id,
            turno_id=existente.id,
        ),
    )
    with fabrica_sesiones() as otra_sesion:
        assert len(otra_sesion.scalars(select(TurnoModelo)).all()) == 1  # solo el existente


def test_e4_doble_conflicto_informa_los_dos_codigos(sesion, fabrica_sesiones, uow):
    datos = _escenario(sesion, duracion_minutos=30)
    existente = un_turno(
        sesion,
        paciente=datos["paciente"],
        profesional=datos["profesional"],
        sillon=datos["sillon"],
        prestacion=datos["prestacion"],
        inicio=a_las(10),
    )
    comando = _comando(datos, a_las(10, 15))

    with pytest.raises(ErrorDeSolapamiento) as excinfo:
        crear_turno(comando, uow, reloj_fijo)

    assert excinfo.value.codigos == ["RN-AG-05", "RN-AG-08"]
    assert excinfo.value.conflictos == (
        Conflicto(
            codigo="RN-AG-05",
            recurso="profesional",
            recurso_id=datos["profesional"].id,
            turno_id=existente.id,
        ),
        Conflicto(
            codigo="RN-AG-08",
            recurso="sillon",
            recurso_id=datos["sillon"].id,
            turno_id=existente.id,
        ),
    )
    with fabrica_sesiones() as otra_sesion:
        assert len(otra_sesion.scalars(select(TurnoModelo)).all()) == 1  # solo el existente


def test_e4_cada_conflicto_lleva_su_propio_turno(sesion, fabrica_sesiones, uow):
    datos = _escenario(sesion, duracion_minutos=30)
    profesional_b = un_profesional(sesion, datos["consultorio"])
    sillon_2 = un_sillon(sesion, datos["consultorio"])
    # X: el profesional pedido, en otro sillón. Y: el sillón pedido, con otro profesional.
    turno_x = un_turno(
        sesion,
        paciente=datos["paciente"],
        profesional=datos["profesional"],
        sillon=sillon_2,
        prestacion=datos["prestacion"],
        inicio=a_las(10),
    )
    turno_y = un_turno(
        sesion,
        paciente=datos["paciente"],
        profesional=profesional_b,
        sillon=datos["sillon"],
        prestacion=datos["prestacion"],
        inicio=a_las(10),
    )
    comando = _comando(datos, a_las(10))

    with pytest.raises(ErrorDeSolapamiento) as excinfo:
        crear_turno(comando, uow, reloj_fijo)

    assert excinfo.value.codigos == ["RN-AG-05", "RN-AG-08"]
    assert excinfo.value.conflictos == (
        Conflicto(
            codigo="RN-AG-05",
            recurso="profesional",
            recurso_id=datos["profesional"].id,
            turno_id=turno_x.id,
        ),
        Conflicto(
            codigo="RN-AG-08",
            recurso="sillon",
            recurso_id=datos["sillon"].id,
            turno_id=turno_y.id,
        ),
    )
    with fabrica_sesiones() as otra_sesion:
        assert len(otra_sesion.scalars(select(TurnoModelo)).all()) == 2  # X e Y, ninguno nuevo


@pytest.mark.parametrize(
    ("inicio_pedido", "fin_esperado"),
    [
        pytest.param(a_las(10, 30), a_las(11), id="empieza_donde_termina_el_existente"),
        pytest.param(a_las(9, 30), a_las(10), id="termina_donde_empieza_el_existente"),
    ],
)
def test_e5_borde_contiguo_se_acepta(
    sesion, fabrica_sesiones, uow, inicio_pedido, fin_esperado
):
    datos = _escenario(sesion, duracion_minutos=30)
    un_turno(
        sesion,
        paciente=datos["paciente"],
        profesional=datos["profesional"],
        sillon=datos["sillon"],
        prestacion=datos["prestacion"],
        inicio=a_las(10),
    )

    turno = crear_turno(_comando(datos, inicio_pedido), uow, reloj_fijo)

    assert turno.id is not None
    assert turno.inicio == inicio_pedido
    assert turno.fin == fin_esperado
    with fabrica_sesiones() as otra_sesion:
        assert len(otra_sesion.scalars(select(TurnoModelo)).all()) == 2  # el existente y el nuevo


def test_e3_profesional_con_turno_a_otra_hora_rechaza_solo_con_rn_ag_08(
    sesion, fabrica_sesiones, uow
):
    datos = _escenario(sesion, duracion_minutos=30)
    profesional_b = un_profesional(sesion, datos["consultorio"])
    sillon_2 = un_sillon(sesion, datos["consultorio"])
    # B tiene un turno a las 14:00 en el sillón 2: no choca con lo pedido a las 10:00.
    un_turno(
        sesion,
        paciente=datos["paciente"],
        profesional=profesional_b,
        sillon=sillon_2,
        prestacion=datos["prestacion"],
        inicio=a_las(14),
    )
    # El sillón 1 está ocupado de 10:00 a 10:30 por el profesional A.
    turno_de_a = un_turno(
        sesion,
        paciente=datos["paciente"],
        profesional=datos["profesional"],
        sillon=datos["sillon"],
        prestacion=datos["prestacion"],
        inicio=a_las(10),
    )
    comando = CrearTurnoComando(
        paciente_id=datos["paciente"].id,
        prestacion_id=datos["prestacion"].id,
        inicio=a_las(10),
        profesional_id=profesional_b.id,
        sillon_id=datos["sillon"].id,
    )

    with pytest.raises(ErrorDeSolapamiento) as excinfo:
        crear_turno(comando, uow, reloj_fijo)

    assert excinfo.value.codigos == ["RN-AG-08"]
    assert excinfo.value.conflictos == (
        Conflicto(
            codigo="RN-AG-08",
            recurso="sillon",
            recurso_id=datos["sillon"].id,
            turno_id=turno_de_a.id,
        ),
    )
    with fabrica_sesiones() as otra_sesion:
        assert len(otra_sesion.scalars(select(TurnoModelo)).all()) == 2  # ninguno nuevo


def test_e5_turno_entre_dos_existentes_contiguos_se_acepta(sesion, fabrica_sesiones, uow):
    datos = _escenario(sesion, duracion_minutos=30)
    for hora, minuto in ((10, 0), (11, 0)):
        un_turno(
            sesion,
            paciente=datos["paciente"],
            profesional=datos["profesional"],
            sillon=datos["sillon"],
            prestacion=datos["prestacion"],
            inicio=a_las(hora, minuto),
        )

    turno = crear_turno(_comando(datos, a_las(10, 30)), uow, reloj_fijo)

    assert turno.inicio == a_las(10, 30)
    assert turno.fin == a_las(11)
    with fabrica_sesiones() as otra_sesion:
        assert len(otra_sesion.scalars(select(TurnoModelo)).all()) == 3  # dos existentes y el nuevo


def test_e7_borde_de_un_minuto_se_rechaza(sesion, fabrica_sesiones, uow):
    datos = _escenario(sesion, duracion_minutos=30)
    sillon_2 = un_sillon(sesion, datos["consultorio"])
    existente = un_turno(
        sesion,
        paciente=datos["paciente"],
        profesional=datos["profesional"],
        sillon=datos["sillon"],
        prestacion=datos["prestacion"],
        inicio=a_las(10),
    )
    comando = CrearTurnoComando(
        paciente_id=datos["paciente"].id,
        prestacion_id=datos["prestacion"].id,
        inicio=a_las(10, 29),  # un minuto antes de que termine el existente (10:30)
        profesional_id=datos["profesional"].id,
        sillon_id=sillon_2.id,
    )

    with pytest.raises(ErrorDeSolapamiento) as excinfo:
        crear_turno(comando, uow, reloj_fijo)

    assert excinfo.value.codigos == ["RN-AG-05"]
    assert excinfo.value.conflictos == (
        Conflicto(
            codigo="RN-AG-05",
            recurso="profesional",
            recurso_id=datos["profesional"].id,
            turno_id=existente.id,
        ),
    )
    with fabrica_sesiones() as otra_sesion:
        assert len(otra_sesion.scalars(select(TurnoModelo)).all()) == 1  # solo el existente


def test_e7_minuto_de_solape_del_otro_lado_se_rechaza(sesion, fabrica_sesiones, uow):
    datos = _escenario(sesion, duracion_minutos=30)
    sillon_2 = un_sillon(sesion, datos["consultorio"])
    existente = un_turno(
        sesion,
        paciente=datos["paciente"],
        profesional=datos["profesional"],
        sillon=datos["sillon"],
        prestacion=datos["prestacion"],
        inicio=a_las(10),
    )
    comando = CrearTurnoComando(
        paciente_id=datos["paciente"].id,
        prestacion_id=datos["prestacion"].id,
        inicio=a_las(9, 31),  # termina a las 10:01, un minuto después de que empieza el existente
        profesional_id=datos["profesional"].id,
        sillon_id=sillon_2.id,
    )

    with pytest.raises(ErrorDeSolapamiento) as excinfo:
        crear_turno(comando, uow, reloj_fijo)

    assert excinfo.value.codigos == ["RN-AG-05"]
    assert excinfo.value.conflictos == (
        Conflicto(
            codigo="RN-AG-05",
            recurso="profesional",
            recurso_id=datos["profesional"].id,
            turno_id=existente.id,
        ),
    )
    with fabrica_sesiones() as otra_sesion:
        assert len(otra_sesion.scalars(select(TurnoModelo)).all()) == 1  # solo el existente


def test_e7_borde_de_un_minuto_sobre_el_sillon_se_rechaza(sesion, fabrica_sesiones, uow):
    datos = _escenario(sesion, duracion_minutos=30)
    profesional_b = un_profesional(sesion, datos["consultorio"])
    existente = un_turno(
        sesion,
        paciente=datos["paciente"],
        profesional=datos["profesional"],
        sillon=datos["sillon"],
        prestacion=datos["prestacion"],
        inicio=a_las(10),
    )
    comando = CrearTurnoComando(
        paciente_id=datos["paciente"].id,
        prestacion_id=datos["prestacion"].id,
        inicio=a_las(10, 29),  # un minuto antes de que termine el existente (10:30)
        profesional_id=profesional_b.id,
        sillon_id=datos["sillon"].id,
    )

    with pytest.raises(ErrorDeSolapamiento) as excinfo:
        crear_turno(comando, uow, reloj_fijo)

    assert excinfo.value.codigos == ["RN-AG-08"]
    assert excinfo.value.conflictos == (
        Conflicto(
            codigo="RN-AG-08",
            recurso="sillon",
            recurso_id=datos["sillon"].id,
            turno_id=existente.id,
        ),
    )
    with fabrica_sesiones() as otra_sesion:
        assert len(otra_sesion.scalars(select(TurnoModelo)).all()) == 1  # solo el existente


@pytest.mark.parametrize(
    "estado",
    ["cancelado_paciente", "cancelado_profesional", "vencido", "atendido", "ausente"],
)
def test_e6_estado_no_activo_no_bloquea(sesion, fabrica_sesiones, uow, estado):
    datos = _escenario(sesion, duracion_minutos=30)
    un_turno(
        sesion,
        paciente=datos["paciente"],
        profesional=datos["profesional"],
        sillon=datos["sillon"],
        prestacion=datos["prestacion"],
        inicio=a_las(10),
        estado=estado,
    )

    turno = crear_turno(_comando(datos, a_las(10)), uow, reloj_fijo)

    assert turno.id is not None
    assert turno.estado == EstadoTurno.RESERVADO
    assert turno.inicio == a_las(10)
    assert turno.fin == a_las(10, 30)
    with fabrica_sesiones() as otra_sesion:
        assert len(otra_sesion.scalars(select(TurnoModelo)).all()) == 2  # el cancelado y el nuevo


def test_e12_recurso_no_encontrado_rechaza_con_rn_gl_04(sesion, fabrica_sesiones, uow):
    datos = _escenario(sesion, duracion_minutos=30)
    comando = CrearTurnoComando(
        paciente_id=datos["paciente"].id,
        prestacion_id=999,
        inicio=a_las(10),
        profesional_id=datos["profesional"].id,
        sillon_id=datos["sillon"].id,
    )

    with pytest.raises(EntradaInvalida) as excinfo:
        crear_turno(comando, uow, reloj_fijo)

    assert excinfo.value.codigos == ["RN-GL-04"]
    assert excinfo.value.referencias == (ReferenciaInvalida("prestacion", 999, "inexistente"),)
    with fabrica_sesiones() as otra_sesion:
        assert otra_sesion.scalars(select(TurnoModelo)).all() == []


def _rechazo_de_entrada(uow, comando: CrearTurnoComando) -> EntradaInvalida:
    with pytest.raises(EntradaInvalida) as excinfo:
        crear_turno(comando, uow, reloj_fijo)
    return excinfo.value


def _sin_turnos_guardados(fabrica_sesiones) -> bool:
    with fabrica_sesiones() as otra_sesion:
        return otra_sesion.scalars(select(TurnoModelo)).all() == []


@pytest.mark.parametrize("recurso", ["paciente", "profesional", "sillon"])
def test_e12_referencia_inexistente_rechaza_con_rn_gl_04(
    sesion, fabrica_sesiones, uow, recurso
):
    datos = _escenario(sesion)
    comando = replace(_comando(datos, a_las(10)), **{f"{recurso}_id": 999})

    error = _rechazo_de_entrada(uow, comando)

    assert error.codigos == ["RN-GL-04"]
    assert error.referencias == (ReferenciaInvalida(recurso, 999, "inexistente"),)
    assert _sin_turnos_guardados(fabrica_sesiones)

