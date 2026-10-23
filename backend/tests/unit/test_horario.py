"""Horario recurrente: validez de las franjas (RN-AG-16) y turno dentro de una franja (RN-AG-04, E10).

Puro: sin base de datos ni HTTP. El consultorio es America/Argentina/Buenos_Aires (UTC-3, sin horario de verano).
"""
from datetime import date, datetime, time, timedelta, timezone

import pytest

from app.domain.agenda.horario import Franja, exigir_dentro_del_horario, validar_franjas
from app.domain.agenda.intervalo import Intervalo
from app.domain.errors import FranjaInvalida, FueraDeHorario

ZONA = "America/Argentina/Buenos_Aires"
LUNES, MARTES, MIERCOLES, JUEVES, SABADO = 0, 1, 2, 3, 5


def franja(dia, desde, hasta, vigente_desde=None, vigente_hasta=None):
    return Franja(
        dia_semana=dia,
        hora_inicio=time.fromisoformat(desde),
        hora_fin=time.fromisoformat(hasta),
        vigente_desde=vigente_desde,
        vigente_hasta=vigente_hasta,
    )


def turno_local(dia_del_mes, desde, hasta, mes=11):
    """Intervalo en UTC de un turno de ``desde`` a ``hasta`` hora del consultorio (UTC-3) de 2026.

    ``hasta`` puede ser ``24:00`` para un turno que termina a la medianoche local.
    """
    base = datetime(2026, mes, dia_del_mes, tzinfo=timezone.utc) + timedelta(hours=3)

    def instante(hora):
        hh, mm = (int(p) for p in hora.split(":"))
        return base + timedelta(hours=hh, minutes=mm)

    return Intervalo(instante(desde), instante(hasta))


# 2026-11-02 es lunes.
LUNES_2 = 2


# --- RN-AG-16: validar_franjas -------------------------------------------------------------------
def test_hor1_dos_franjas_superpuestas_del_mismo_dia_devuelven_rn_ag_16_en_la_posicion_1():
    errores = validar_franjas([franja(MIERCOLES, "09:00", "13:00"), franja(MIERCOLES, "12:00", "16:00")])

    assert [(e.campo, e.codigo, e.mensaje) for e in errores] == [
        ("franjas.1", "RN-AG-16", "franjas.1 se superpone con otra franja del mismo día")
    ]


def test_hor1_una_franja_invertida_o_de_duracion_cero_devuelve_rn_ag_16():
    invertida = validar_franjas([franja(JUEVES, "18:00", "09:00")])
    cero = validar_franjas([franja(LUNES, "09:00", "09:00")])

    assert [(e.campo, e.codigo, e.mensaje) for e in invertida] == [
        ("franjas.0", "RN-AG-16", "franjas.0 debe terminar después de empezar")
    ]
    assert [(e.campo, e.mensaje) for e in cero] == [("franjas.0", "franjas.0 debe terminar después de empezar")]


def test_us002_ca1_manana_y_tarde_del_mismo_dia_son_validas():
    assert validar_franjas([franja(LUNES, "15:00", "19:00"), franja(LUNES, "09:00", "13:00")]) == ()


def test_us002_ca2_un_turno_que_excede_el_fin_de_la_franja_levanta_fuera_de_horario_con_rn_ag_04():
    # E10: franja 09:00-13:00; el turno 12:45-13:15 se pasa 15 minutos.
    with pytest.raises(FueraDeHorario) as error:
        exigir_dentro_del_horario(
            turno_local(LUNES_2, "12:45", "13:15"), [franja(LUNES, "09:00", "13:00")], ZONA
        )

    assert error.value.codigos == ["RN-AG-04"]


def test_e10_un_turno_dentro_de_la_franja_no_levanta_nada():
    exigir_dentro_del_horario(
        turno_local(LUNES_2, "10:00", "10:30"), [franja(LUNES, "09:00", "13:00")], ZONA
    )


# --- E10: bordes de RN-AG-04 ---------------------------------------------------------------------
MANANA = [franja(LUNES, "09:00", "13:00")]


@pytest.mark.parametrize(("desde", "hasta"), [("09:00", "09:30"), ("12:30", "13:00"), ("09:00", "13:00")])
def test_e10_empezar_o_terminar_justo_en_el_limite_se_acepta(desde, hasta):
    exigir_dentro_del_horario(turno_local(LUNES_2, desde, hasta), MANANA, ZONA)


@pytest.mark.parametrize(
    ("dia", "desde", "hasta"),
    [
        (LUNES_2, "08:30", "09:15"),  # empieza antes de la franja
        (LUNES_2, "12:45", "13:15"),  # termina después
        (LUNES_2, "13:00", "13:30"),  # justo después de terminar
        (LUNES_2, "14:00", "14:30"),  # entre franjas (hay otra a la tarde)
        (3, "10:00", "10:30"),  # martes: día sin franjas
    ],
)
def test_e10_antes_de_la_franja_entre_franjas_y_en_un_dia_sin_franjas_se_rechaza(dia, desde, hasta):
    franjas = [*MANANA, franja(LUNES, "15:00", "19:00")]

    with pytest.raises(FueraDeHorario):
        exigir_dentro_del_horario(turno_local(dia, desde, hasta), franjas, ZONA)


def test_e10_sin_franjas_no_se_admite_ningun_turno():
    with pytest.raises(FueraDeHorario) as error:
        exigir_dentro_del_horario(turno_local(LUNES_2, "10:00", "10:30"), [], ZONA)

    assert error.value.codigos == ["RN-AG-04"]


def test_e10_el_dia_es_el_del_consultorio_y_no_el_de_utc():
    # Lunes 21:30 local = martes 00:30 UTC: la franja es del lunes.
    lunes_noche = [franja(LUNES, "20:00", "23:00")]
    martes_utc = Intervalo(
        datetime(2026, 11, 3, 0, 30, tzinfo=timezone.utc), datetime(2026, 11, 3, 1, 0, tzinfo=timezone.utc)
    )

    exigir_dentro_del_horario(martes_utc, lunes_noche, ZONA)
    with pytest.raises(FueraDeHorario):
        exigir_dentro_del_horario(martes_utc, [franja(1, "20:00", "23:00")], ZONA)


def test_e10_pasar_de_una_franja_a_otra_contigua_se_rechaza():
    # D258: una sola franja; 09-13 y 13-17 no se suman.
    contiguas = [franja(LUNES, "09:00", "13:00"), franja(LUNES, "13:00", "17:00")]

    with pytest.raises(FueraDeHorario):
        exigir_dentro_del_horario(turno_local(LUNES_2, "12:45", "13:15"), contiguas, ZONA)


def test_e10_una_franja_fuera_de_vigencia_no_cuenta():
    # D259. El turno es el lunes 2026-11-02.
    el_dia = date(2026, 11, 2)
    turno = turno_local(LUNES_2, "10:00", "10:30")

    for vigencia in (
        {"vigente_hasta": date(2026, 11, 1)},
        {"vigente_desde": date(2026, 11, 3)},
    ):
        with pytest.raises(FueraDeHorario):
            exigir_dentro_del_horario(turno, [franja(LUNES, "09:00", "13:00", **vigencia)], ZONA)
    # La fecha justa en cada límite se acepta.
    exigir_dentro_del_horario(turno, [franja(LUNES, "09:00", "13:00", vigente_hasta=el_dia)], ZONA)
    exigir_dentro_del_horario(turno, [franja(LUNES, "09:00", "13:00", vigente_desde=el_dia)], ZONA)


def test_e10_un_turno_que_termina_justo_a_las_0000_del_consultorio_levanta_fuera_de_horario():
    # D265: hora_fin llega a 23:59, así que 23:30-00:00 nunca cabe; 23:00-23:30 sí.
    todo_el_dia = [franja(LUNES, "00:00", "23:59")]

    with pytest.raises(FueraDeHorario) as error:
        exigir_dentro_del_horario(turno_local(LUNES_2, "23:30", "24:00"), todo_el_dia, ZONA)
    assert error.value.codigos == ["RN-AG-04"]
    exigir_dentro_del_horario(turno_local(LUNES_2, "23:00", "23:30"), todo_el_dia, ZONA)


# --- HOR-1: bordes de validar_franjas ------------------------------------------------------------
def test_us002_ca1_franjas_contiguas_y_el_mismo_horario_en_dias_distintos_son_validos():
    assert validar_franjas([franja(LUNES, "09:00", "13:00"), franja(LUNES, "13:00", "17:00")]) == ()
    assert validar_franjas([franja(LUNES, "09:00", "13:00"), franja(MARTES, "09:00", "13:00")]) == ()


def test_hor1_dos_franjas_identicas_del_mismo_dia_se_superponen():
    errores = validar_franjas([franja(LUNES, "09:00", "13:00"), franja(LUNES, "09:00", "13:00")])

    assert [e.campo for e in errores] == ["franjas.1"]


def test_hor1_en_una_cadena_de_tres_franjas_del_mismo_dia_se_informan_las_dos_posteriores():
    # D266: la 15-19 se superpone con la 12-16 aunque esta ya se haya informado.
    errores = validar_franjas(
        [franja(MIERCOLES, "09:00", "13:00"), franja(MIERCOLES, "12:00", "16:00"), franja(MIERCOLES, "15:00", "19:00")]
    )

    assert [(e.campo, e.mensaje) for e in errores] == [
        ("franjas.1", "franjas.1 se superpone con otra franja del mismo día"),
        ("franjas.2", "franjas.2 se superpone con otra franja del mismo día"),
    ]


def test_hor1_superposiciones_de_varios_dias_y_una_invertida_se_informan_juntas_en_el_orden_del_cuerpo():
    errores = validar_franjas(
        [
            franja(LUNES, "09:00", "13:00"),
            franja(LUNES, "12:59", "14:00"),
            franja(MARTES, "10:00", "11:00"),
            franja(MARTES, "10:30", "10:45"),
            franja(JUEVES, "18:00", "09:00"),
        ]
    )

    assert [(e.campo, e.mensaje) for e in errores] == [
        ("franjas.1", "franjas.1 se superpone con otra franja del mismo día"),
        ("franjas.3", "franjas.3 se superpone con otra franja del mismo día"),
        ("franjas.4", "franjas.4 debe terminar después de empezar"),
    ]
    assert {e.codigo for e in errores} == {"RN-AG-16"}


def test_hor1_una_franja_invertida_no_se_compara_con_las_demas():
    # Con la formula del solape, la invertida 12:00-10:00 "chocaria" con la 09:00-13:00: no debe informarse esta.
    errores = validar_franjas([franja(LUNES, "12:00", "10:00"), franja(LUNES, "09:00", "13:00")])

    assert [e.campo for e in errores] == ["franjas.0"]


def test_hor1_se_compara_con_todas_las_anteriores_del_dia_y_no_solo_con_la_inmediata():
    # La tercera (12-16) se superpone con la primera (09-13), no con la segunda (14-15 intercalada).
    errores = validar_franjas(
        [franja(LUNES, "09:00", "13:00"), franja(LUNES, "14:00", "15:00"), franja(LUNES, "12:00", "14:00")]
    )

    assert [e.campo for e in errores] == ["franjas.2"]
