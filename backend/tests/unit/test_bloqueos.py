"""Bloqueos: alcance, fechas (RN-AG-17), turnos afectados (US-003 CA-2) y turno sobre un bloqueo (RN-AG-04b, E10).

Puro: sin base de datos ni HTTP. Los horarios son UTC del lunes 2026-11-02 (``a_las``).
"""
from dataclasses import replace
from datetime import datetime

import pytest

from app.domain.agenda.bloqueos import (
    Alcance,
    DatosBloqueo,
    afecta_al_turno,
    exigir_sin_bloqueos,
    turnos_afectados,
    validar_fechas_del_bloqueo,
)
from app.domain.agenda.intervalo import Intervalo
from app.domain.errors import BloqueoInvertido, SobreBloqueo
from app.domain.turnos.estados import EstadoTurno
from app.domain.turnos.turno import Turno
from tests.conftest import RELOJ_FIJO, a_las

CONSULTORIO, OTRO_CONSULTORIO = 1, 2
PROFESIONAL, OTRO_PROFESIONAL = 1, 2
SILLON, OTRO_SILLON = 1, 2


def un_bloqueo(
    desde: datetime,
    hasta: datetime,
    *,
    id: int | None = 1,
    profesional_id: int | None = None,
    sillon_id: int | None = None,
    consultorio_id: int = CONSULTORIO,
) -> DatosBloqueo:
    return DatosBloqueo(
        id=id,
        consultorio_id=consultorio_id,
        profesional_id=profesional_id,
        sillon_id=sillon_id,
        inicio=desde,
        fin=hasta,
        motivo="Ausencia",
        creado_por=1,
    )


def un_turno(
    id: int,
    desde: datetime,
    hasta: datetime,
    *,
    estado: EstadoTurno = EstadoTurno.RESERVADO,
    profesional_id: int = PROFESIONAL,
    sillon_id: int = SILLON,
    consultorio_id: int = CONSULTORIO,
) -> Turno:
    return Turno(
        id=id,
        consultorio_id=consultorio_id,
        paciente_id=1,
        profesional_id=profesional_id,
        sillon_id=sillon_id,
        prestacion_id=1,
        inicio=desde,
        fin=hasta,
        duracion_minutos=int((hasta - desde).total_seconds() // 60),
        estado=estado,
        creado_en=RELOJ_FIJO,
    )


BLOQUEO = un_bloqueo(a_las(12), a_las(16), profesional_id=PROFESIONAL)


# --- Alcance ---------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("profesional_id", "sillon_id", "esperado"),
    [
        (PROFESIONAL, None, Alcance.PROFESIONAL),
        (None, SILLON, Alcance.SILLON),
        (None, None, Alcance.CONSULTORIO),
    ],
)
def test_us003_ca1_el_alcance_es_profesional_sillon_o_consultorio_segun_los_ids(
    profesional_id, sillon_id, esperado
):
    bloqueo = un_bloqueo(a_las(12), a_las(16), profesional_id=profesional_id, sillon_id=sillon_id)

    assert bloqueo.alcance is esperado


# --- RN-AG-17 --------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("inicio", "fin"),
    [(a_las(15), a_las(13)), (a_las(13), a_las(13)), (a_las(13, 1), a_las(13))],
)
def test_us003_ca1_un_bloqueo_que_no_termina_despues_de_empezar_levanta_bloqueo_invertido_con_rn_ag_17(
    inicio, fin
):
    with pytest.raises(BloqueoInvertido) as error:
        validar_fechas_del_bloqueo(inicio, fin)

    assert error.value.codigos == ["RN-AG-17"]
    assert error.value.campo == "fin"
    assert error.value.mensaje == "fin debe ser posterior a inicio"


@pytest.mark.parametrize(("inicio", "fin"), [(a_las(13), a_las(14)), (a_las(13), a_las(13, 1))])
def test_us003_ca1_un_bloqueo_que_termina_despues_de_empezar_no_levanta_nada(inicio, fin):
    validar_fechas_del_bloqueo(inicio, fin)


# --- US-003 CA-2: turnos afectados -----------------------------------------------------------------
def test_us003_ca2_un_bloqueo_del_profesional_lista_sus_turnos_activos_que_intersecan_por_inicio():
    tarde = un_turno(2, a_las(14), a_las(14, 30), estado=EstadoTurno.CONFIRMADO)
    temprano = un_turno(1, a_las(13), a_las(13, 30))
    de_otro_profesional = un_turno(3, a_las(13), a_las(13, 30), profesional_id=OTRO_PROFESIONAL)

    afectados = turnos_afectados(BLOQUEO, [tarde, temprano, de_otro_profesional])

    assert [t.id for t in afectados] == [1, 2]


@pytest.mark.parametrize(
    "estado",
    [
        EstadoTurno.CANCELADO_PACIENTE,
        EstadoTurno.CANCELADO_PROFESIONAL,
        EstadoTurno.VENCIDO,
        EstadoTurno.ATENDIDO,
        EstadoTurno.AUSENTE,
    ],
)
def test_us003_ca2_los_turnos_no_activos_no_se_listan(estado):
    assert turnos_afectados(BLOQUEO, [un_turno(1, a_las(13), a_las(13, 30), estado=estado)]) == ()


@pytest.mark.parametrize(
    "estado",
    [
        EstadoTurno.PENDIENTE_APROBACION,
        EstadoTurno.PENDIENTE_SENA,
        EstadoTurno.RESERVADO,
        EstadoTurno.CONFIRMADO,
    ],
)
def test_us003_ca2_los_cuatro_estados_activos_se_listan(estado):
    turno = un_turno(1, a_las(13), a_las(13, 30), estado=estado)

    assert turnos_afectados(BLOQUEO, [turno]) == (turno,)


def test_us003_ca2_los_contiguos_no_se_listan_y_un_minuto_de_interseccion_si():
    termina_justo = un_turno(1, a_las(11, 30), a_las(12))
    empieza_justo = un_turno(2, a_las(16), a_las(16, 30))
    un_minuto_al_final = un_turno(3, a_las(15, 59), a_las(16, 29))
    un_minuto_al_inicio = un_turno(4, a_las(11, 31), a_las(12, 1))

    afectados = turnos_afectados(BLOQUEO, [termina_justo, empieza_justo, un_minuto_al_final, un_minuto_al_inicio])

    assert [t.id for t in afectados] == [4, 3]


def test_us003_ca2_el_bloqueo_del_sillon_lista_los_turnos_de_ese_sillon_de_cualquier_profesional():
    bloqueo = un_bloqueo(a_las(12), a_las(16), sillon_id=SILLON)
    en_el_sillon = un_turno(1, a_las(13), a_las(13, 30), profesional_id=OTRO_PROFESIONAL)
    en_otro_sillon = un_turno(2, a_las(13), a_las(13, 30), sillon_id=OTRO_SILLON)

    assert turnos_afectados(bloqueo, [en_el_sillon, en_otro_sillon]) == (en_el_sillon,)


def test_us003_ca2_el_bloqueo_del_consultorio_lista_todos_sus_turnos_y_ninguno_de_otro_consultorio():
    bloqueo = un_bloqueo(a_las(12), a_las(16))
    uno = un_turno(1, a_las(13), a_las(13, 30))
    otro = un_turno(2, a_las(14), a_las(14, 30), profesional_id=OTRO_PROFESIONAL, sillon_id=OTRO_SILLON)
    ajeno = un_turno(3, a_las(13), a_las(13, 30), consultorio_id=OTRO_CONSULTORIO)

    assert turnos_afectados(bloqueo, [ajeno, otro, uno]) == (uno, otro)


def test_us003_ca2_con_dos_turnos_a_la_misma_hora_se_ordenan_por_id():
    mayor = un_turno(9, a_las(13), a_las(13, 30))
    menor = un_turno(4, a_las(13), a_las(13, 30), profesional_id=PROFESIONAL)

    assert [t.id for t in turnos_afectados(BLOQUEO, [mayor, menor])] == [4, 9]


def test_us003_ca2_afecta_al_turno_compara_el_alcance_y_la_interseccion():
    turno = un_turno(1, a_las(13), a_las(13, 30))

    assert afecta_al_turno(BLOQUEO, turno)
    assert not afecta_al_turno(replace(BLOQUEO, profesional_id=OTRO_PROFESIONAL), turno)
    assert not afecta_al_turno(replace(BLOQUEO, inicio=a_las(13, 30), fin=a_las(15)), turno)


# --- E10: RN-AG-04b ---------------------------------------------------------------------------------
def _exigir(intervalo: Intervalo, bloqueos, profesional_id=PROFESIONAL, sillon_id=SILLON):
    exigir_sin_bloqueos(intervalo, profesional_id, sillon_id, CONSULTORIO, bloqueos)


def test_e10_un_turno_dentro_de_un_bloqueo_del_profesional_levanta_sobre_bloqueo_con_rn_ag_04b_y_el_bloqueo_id():
    bloqueo = un_bloqueo(a_las(10), a_las(12), id=7, profesional_id=PROFESIONAL)

    with pytest.raises(SobreBloqueo) as error:
        _exigir(Intervalo(a_las(10, 30), a_las(11)), [bloqueo])

    assert error.value.codigos == ["RN-AG-04b"]
    assert error.value.bloqueo_id == 7


def test_e10_un_turno_fuera_de_todo_bloqueo_no_levanta_nada():
    bloqueos = [
        un_bloqueo(a_las(10), a_las(12), id=1, profesional_id=PROFESIONAL),
        un_bloqueo(a_las(14), a_las(16), id=2),
    ]

    _exigir(Intervalo(a_las(12), a_las(14)), bloqueos)
    _exigir(Intervalo(a_las(8), a_las(10)), bloqueos)
    _exigir(Intervalo(a_las(12), a_las(14)), [])


@pytest.mark.parametrize(
    "bloqueo",
    [
        un_bloqueo(a_las(10), a_las(12), id=3, sillon_id=SILLON),
        un_bloqueo(a_las(10), a_las(12), id=3),
    ],
    ids=["sillon", "consultorio"],
)
def test_e10_un_bloqueo_del_sillon_o_del_consultorio_tambien_rechaza_el_turno(bloqueo):
    with pytest.raises(SobreBloqueo) as error:
        _exigir(Intervalo(a_las(11), a_las(11, 30)), [bloqueo], profesional_id=OTRO_PROFESIONAL)

    assert error.value.bloqueo_id == 3


@pytest.mark.parametrize(
    "bloqueo",
    [
        un_bloqueo(a_las(10), a_las(12), profesional_id=OTRO_PROFESIONAL),
        un_bloqueo(a_las(10), a_las(12), sillon_id=OTRO_SILLON),
        un_bloqueo(a_las(10), a_las(12), consultorio_id=OTRO_CONSULTORIO),
    ],
    ids=["otro-profesional", "otro-sillon", "otro-consultorio"],
)
def test_e10_un_bloqueo_de_otro_profesional_o_de_otro_sillon_no_lo_afecta(bloqueo):
    _exigir(Intervalo(a_las(11), a_las(11, 30)), [bloqueo])


def test_e10_un_turno_contiguo_al_bloqueo_se_acepta_y_un_minuto_adentro_se_rechaza():
    bloqueo = un_bloqueo(a_las(10), a_las(12), profesional_id=PROFESIONAL)

    _exigir(Intervalo(a_las(9, 30), a_las(10)), [bloqueo])
    _exigir(Intervalo(a_las(12), a_las(12, 30)), [bloqueo])
    for adentro in (Intervalo(a_las(9, 31), a_las(10, 1)), Intervalo(a_las(11, 59), a_las(12, 29))):
        with pytest.raises(SobreBloqueo):
            _exigir(adentro, [bloqueo])


def test_e10_con_dos_bloqueos_que_lo_intersecan_se_informa_el_que_empieza_primero():
    consultorio = un_bloqueo(a_las(11), a_las(12), id=1)
    profesional = un_bloqueo(a_las(10), a_las(12), id=2, profesional_id=PROFESIONAL)

    with pytest.raises(SobreBloqueo) as error:
        _exigir(Intervalo(a_las(11), a_las(11, 30)), [consultorio, profesional])

    assert error.value.bloqueo_id == 2


def test_e10_con_dos_bloqueos_que_empiezan_a_la_misma_hora_se_informa_el_de_menor_id():
    mayor = un_bloqueo(a_las(10), a_las(12), id=9, profesional_id=PROFESIONAL)
    menor = un_bloqueo(a_las(10), a_las(13), id=4, profesional_id=PROFESIONAL)

    with pytest.raises(SobreBloqueo) as error:
        _exigir(Intervalo(a_las(11), a_las(11, 30)), [mayor, menor])

    assert error.value.bloqueo_id == 4
