"""Caso de uso ``reprogramar_turno`` con repositorio real sobre SQLite en memoria (C-16; US-012, DD-05)."""
from datetime import datetime

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.exc import DBAPIError

from app.application.crear_turno import CrearTurnoComando, crear_turno
from app.application.historial import consultar_historial
from app.application.reprogramar_turno import ReprogramarTurnoComando, reprogramar_turno
from app.domain.errors import (
    Conflicto,
    EntradaInvalida,
    ErrorDeSolapamiento,
    FueraDeHorario,
    IntervaloInvalido,
    SobreBloqueo,
    TurnoNoEncontrado,
    TurnoNoReprogramable,
)
from app.domain.tiempo import UTC
from app.domain.turnos.eventos import Actor, ActorTipo, TipoEvento
from app.infrastructure.db.modelos import EventoTurnoModelo, TurnoModelo
from tests.conftest import RELOJ_FIJO, a_las, reloj_fijo
from tests.factories import (
    ACTOR_DE_PRUEBA,
    ID_DE_USUARIO_DE_PRUEBA,
    franja,
    un_bloqueo,
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
    un_usuario,
)

RECEPCIONISTA = Actor(ActorTipo.USUARIO, "2")


def _escenario(sesion, duracion_minutos: int = 30, **kw) -> dict:
    consultorio = un_consultorio(sesion)
    return {
        "consultorio": consultorio,
        "usuario": un_usuario(sesion, consultorio),
        "paciente": un_paciente(sesion, consultorio),
        "profesional": un_profesional(sesion, consultorio, **kw),
        "sillon": un_sillon(sesion, consultorio),
        "prestacion": una_prestacion(sesion, consultorio, duracion_minutos=duracion_minutos),
    }


def _crear(uow, datos: dict, inicio, paciente=None):
    return crear_turno(
        CrearTurnoComando(
            paciente_id=(paciente or datos["paciente"]).id,
            prestacion_id=datos["prestacion"].id,
            inicio=inicio,
            profesional_id=datos["profesional"].id,
            sillon_id=datos["sillon"].id,
        ),
        uow,
        reloj_fijo,
        actor=ACTOR_DE_PRUEBA,
        creado_por=ID_DE_USUARIO_DE_PRUEBA,
    )


def _reprogramar(uow, datos: dict, turno_id: int, inicio=None, duracion_minutos=None):
    return reprogramar_turno(
        ReprogramarTurnoComando(turno_id, inicio, duracion_minutos),
        datos["usuario"].id,
        uow,
        reloj_fijo,
        actor=RECEPCIONISTA,
    )


def test_rep1a_reprogramar_mueve_el_mismo_turno(sesion, uow):
    datos = _escenario(sesion)
    original = _crear(uow, datos, a_las(13))

    movido = _reprogramar(uow, datos, original.id, inicio=a_las(17))

    assert movido.id == original.id
    assert movido.inicio == a_las(17)
    assert movido.fin == a_las(17, 30)
    assert movido.duracion_minutos == 30
    assert movido.estado == original.estado
    assert movido.paciente_id == original.paciente_id
    assert movido.prestacion_id == original.prestacion_id
    assert movido.profesional_id == original.profesional_id
    assert movido.sillon_id == original.sillon_id
    assert movido.creado_en == original.creado_en
    assert sesion.scalar(select(func.count()).select_from(TurnoModelo)) == 1


def test_rep2a_reprogramar_registra_el_evento(sesion, uow):
    datos = _escenario(sesion)
    original = _crear(uow, datos, a_las(13))

    _reprogramar(uow, datos, original.id, inicio=a_las(17), duracion_minutos=45)

    eventos = consultar_historial(original.id, uow)
    assert [e.tipo for e in eventos] == [TipoEvento.CREADO, TipoEvento.REPROGRAMADO]
    reprogramado = eventos[1]
    assert reprogramado.actor_id == "2"
    assert reprogramado.ocurrido_en == RELOJ_FIJO
    assert reprogramado.antes == {
        "inicio": "2026-11-02T13:00:00Z", "fin": "2026-11-02T13:30:00Z", "duracion_minutos": 30,
    }
    assert reprogramado.despues == {
        "inicio": "2026-11-02T17:00:00Z", "fin": "2026-11-02T17:45:00Z", "duracion_minutos": 45,
    }


HORARIO_8_A_20 = tuple(franja(dia, "08:00", "20:00") for dia in range(5))  # lunes a viernes


def _poner_estado(sesion, turno_id: int, estado: str) -> None:
    sesion.execute(update(TurnoModelo).where(TurnoModelo.id == turno_id).values(estado=estado))
    sesion.commit()


def _de_otro(sesion, datos, inicio, estado="reservado", minutos=45):
    """Un turno de Bruno guardado directo (sin pasar por las reglas), del mismo profesional y sillón."""
    bruno = un_paciente(sesion, datos["consultorio"], nombre="Bruno", apellido="Ficticio")
    prestacion = una_prestacion(sesion, datos["consultorio"], duracion_minutos=minutos)
    return un_turno(
        sesion,
        paciente=bruno,
        profesional=datos["profesional"],
        sillon=datos["sillon"],
        prestacion=prestacion,
        inicio=inicio,
        estado=estado,
    )


def _horario_de(uow, turno_id: int):
    with uow:
        t = uow.agenda.turno_para_cambiar(turno_id)
        return t.inicio, t.fin, t.duracion_minutos, t.estado.value


def _tipos(uow, turno_id: int) -> list[str]:
    return [e.tipo.value for e in consultar_historial(turno_id, uow)]


@pytest.mark.parametrize(
    ("inicio_nuevo", "fin_esperado"),
    [(a_las(13, 15), a_las(13, 45)), (a_las(13, 30), a_las(14))],
)
def test_rep1b_sobre_su_propio_horario_y_pegado_al_siguiente(sesion, uow, inicio_nuevo, fin_esperado):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    bruno = _de_otro(sesion, datos, a_las(14))

    movido = _reprogramar(uow, datos, ana.id, inicio=inicio_nuevo)

    assert (movido.inicio, movido.fin) == (inicio_nuevo, fin_esperado)
    assert _horario_de(uow, bruno.id)[:2] == (a_las(14), a_las(14, 45))


def test_rep1c_sobre_otro_turno_activo_conflicto_doble_y_no_cambia(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    bruno = _de_otro(sesion, datos, a_las(14), estado="confirmado")

    with pytest.raises(ErrorDeSolapamiento) as error:
        _reprogramar(uow, datos, ana.id, inicio=a_las(14, 15))

    assert error.value.codigos == ["RN-AG-05", "RN-AG-08"]
    assert error.value.conflictos == (
        Conflicto("RN-AG-05", "profesional", datos["profesional"].id, bruno.id),
        Conflicto("RN-AG-08", "sillon", datos["sillon"].id, bruno.id),
    )
    assert _horario_de(uow, ana.id)[:3] == (a_las(13), a_las(13, 30), 30)
    assert _tipos(uow, ana.id) == ["creado"]


def test_rep1c_un_turno_cancelado_libera_el_horario(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    _de_otro(sesion, datos, a_las(14), estado="cancelado_paciente")

    movido = _reprogramar(uow, datos, ana.id, inicio=a_las(14, 15))

    assert (movido.inicio, movido.fin) == (a_las(14, 15), a_las(14, 45))


@pytest.mark.parametrize(
    ("inicio_nuevo", "excepcion", "codigo"),
    [
        (datetime(2026, 11, 3, 2, 45, tzinfo=UTC), IntervaloInvalido, "RN-AG-10d"),
        (datetime(2026, 11, 2, 10, 30, tzinfo=UTC), FueraDeHorario, "RN-AG-04"),
        (datetime(2026, 11, 7, 13, 0, tzinfo=UTC), FueraDeHorario, "RN-AG-04"),
        (datetime(2026, 11, 3, 13, 0, tzinfo=UTC), SobreBloqueo, "RN-AG-04b"),
    ],
)
def test_rep1d_las_reglas_de_un_turno_nuevo_de_a_una(sesion, uow, inicio_nuevo, excepcion, codigo):
    datos = _escenario(sesion, horario=HORARIO_8_A_20)
    ana = _crear(uow, datos, a_las(13))
    bloqueo = un_bloqueo(
        sesion,
        datos["consultorio"],
        inicio=datetime(2026, 11, 3, 12, tzinfo=UTC),
        fin=datetime(2026, 11, 3, 15, tzinfo=UTC),
    )

    with pytest.raises(excepcion) as error:
        _reprogramar(uow, datos, ana.id, inicio=inicio_nuevo)

    assert error.value.codigos == [codigo]
    if excepcion is SobreBloqueo:
        assert error.value.bloqueo_id == bloqueo.id
    assert _horario_de(uow, ana.id)[:3] == (a_las(13), a_las(13, 30), 30)
    assert _tipos(uow, ana.id) == ["creado"]


def test_rep1d_horario_y_solapamiento_a_la_vez_solo_informa_el_horario(sesion, uow):
    datos = _escenario(sesion, horario=HORARIO_8_A_20)
    ana = _crear(uow, datos, a_las(13))
    _de_otro(sesion, datos, a_las(10, 30), minutos=30)  # 07:30 a 08:00 del consultorio, guardado sin regla (D261)

    with pytest.raises(FueraDeHorario) as error:
        _reprogramar(uow, datos, ana.id, inicio=a_las(10, 30))

    assert error.value.codigos == ["RN-AG-04"]


def test_rep2b_un_rechazo_no_registra_eventos(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    _de_otro(sesion, datos, a_las(14))

    with pytest.raises(ErrorDeSolapamiento):
        _reprogramar(uow, datos, ana.id, inicio=a_las(14, 15))
    with pytest.raises(EntradaInvalida):
        _reprogramar(uow, datos, ana.id, duracion_minutos=42)

    assert _tipos(uow, ana.id) == ["creado"]


def test_rep2b_si_el_evento_falla_el_turno_no_se_mueve(sesion, engine, fabrica_sesiones, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    with engine.begin() as conexion:  # falla real de la base, sin dobles (como E9 de C-03)
        conexion.exec_driver_sql(
            "CREATE TRIGGER evento_turno_falla BEFORE INSERT ON evento_turno "
            "BEGIN SELECT RAISE(ABORT, 'falla de prueba al registrar el evento'); END"
        )

    with pytest.raises(DBAPIError, match="falla de prueba al registrar el evento"):
        _reprogramar(uow, datos, ana.id, inicio=a_las(17))

    assert _horario_de(uow, ana.id)[:2] == (a_las(13), a_las(13, 30))
    with fabrica_sesiones() as otra:
        assert otra.scalar(select(func.count()).select_from(EventoTurnoModelo)) == 1


def test_rep3a_alargar_sin_mover(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))

    alargado = _reprogramar(uow, datos, ana.id, duracion_minutos=60)

    assert (alargado.inicio, alargado.fin, alargado.duracion_minutos) == (a_las(13), a_las(14), 60)
    assert datos["prestacion"].duracion_minutos == 30


def test_rep3a_alargar_contra_el_turno_siguiente_da_409(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    _de_otro(sesion, datos, a_las(13, 45))

    with pytest.raises(ErrorDeSolapamiento) as error:
        _reprogramar(uow, datos, ana.id, duracion_minutos=60)

    assert error.value.codigos == ["RN-AG-05", "RN-AG-08"]
    assert _horario_de(uow, ana.id)[2] == 30


@pytest.mark.parametrize("duracion", [42, 0, -5])
def test_rep3b_duracion_que_no_es_multiplo_de_5(sesion, uow, duracion):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))

    with pytest.raises(EntradaInvalida) as error:
        _reprogramar(uow, datos, ana.id, duracion_minutos=duracion)

    assert error.value.codigos == ["RN-AG-01"]
    assert _horario_de(uow, ana.id)[:3] == (a_las(13), a_las(13, 30), 30)


def test_rep3b_inicio_sin_zona_y_duracion_invalida_dan_los_dos_codigos_juntos(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))

    with pytest.raises(EntradaInvalida) as error:
        _reprogramar(uow, datos, ana.id, inicio=datetime(2026, 11, 2, 14), duracion_minutos=42)

    assert error.value.codigos == ["RN-GL-01", "RN-AG-01"]


def test_rep3b_cinco_minutos_es_valida(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))

    assert _reprogramar(uow, datos, ana.id, duracion_minutos=5).fin == a_las(13, 5)


@pytest.mark.parametrize("duracion", [1445, 1_000_000_000])
def test_rep3c_una_duracion_desmedida_es_rn_ag_01_y_no_cambia(sesion, uow, duracion):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))

    with pytest.raises(EntradaInvalida) as error:
        _reprogramar(uow, datos, ana.id, duracion_minutos=duracion)

    assert error.value.codigos == ["RN-AG-01"]
    assert _horario_de(uow, ana.id)[:3] == (a_las(13), a_las(13, 30), 30)
    assert _tipos(uow, ana.id) == ["creado"]


def test_rep3c_1440_pasa_la_entrada_y_da_rn_ag_10d(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))

    with pytest.raises(IntervaloInvalido) as error:
        _reprogramar(uow, datos, ana.id, duracion_minutos=1440)

    assert error.value.codigos == ["RN-AG-10d"]


@pytest.mark.parametrize(
    ("inicio", "duracion"), [(None, None), (a_las(13), 30), (a_las(13), None), (None, 30)]
)
def test_rep4c_sin_cambios_no_evalua_reglas_ni_registra_evento(sesion, uow, inicio, duracion):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    un_bloqueo(  # creado después del turno (D83): evaluar las reglas daría RN-AG-04b
        sesion, datos["consultorio"], inicio=a_las(12), fin=a_las(15)
    )

    resultado = _reprogramar(uow, datos, ana.id, inicio=inicio, duracion_minutos=duracion)

    assert (resultado.inicio, resultado.fin) == (a_las(13), a_las(13, 30))
    assert _tipos(uow, ana.id) == ["creado"]


def test_rep4b_inexistente_y_de_otro_consultorio_son_404_y_antes_que_la_duracion(sesion, uow):
    datos = _escenario(sesion)
    ajeno = _escenario(sesion)
    del_otro = _de_otro(sesion, ajeno, a_las(13))

    for turno_id in (999, del_otro.id):
        with pytest.raises(TurnoNoEncontrado):
            _reprogramar(uow, datos, turno_id, duracion_minutos=42)  # la duración no se mira antes


@pytest.mark.parametrize(
    "estado",
    ["cancelado_paciente", "cancelado_profesional", "vencido", "atendido", "ausente"],
)
def test_rep5a_un_terminal_se_rechaza_y_no_cambia(sesion, uow, estado):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    _poner_estado(sesion, ana.id, estado)

    with pytest.raises(TurnoNoReprogramable) as error:
        _reprogramar(uow, datos, ana.id, inicio=a_las(19))

    assert error.value.codigos == ["RN-AG-18"]
    assert _horario_de(uow, ana.id) == (a_las(13), a_las(13, 30), 30, estado)


@pytest.mark.parametrize(
    ("estado", "hora"),
    [("pendiente_aprobacion", 14), ("pendiente_sena", 15), ("reservado", 16), ("confirmado", 17)],
)
def test_rep5a_un_activo_se_mueve_sin_cambiar_su_estado(sesion, uow, estado, hora):
    datos = _escenario(sesion)
    bruno = _de_otro(sesion, datos, a_las(hora), estado=estado, minutos=30)

    movido = _reprogramar(uow, datos, bruno.id, inicio=a_las(hora, 30))

    assert movido.estado.value == estado
    assert movido.inicio == a_las(hora, 30)


def test_rep5a_un_turno_pasado_se_reprograma(sesion, uow):
    datos = _escenario(sesion)
    pasado = _de_otro(sesion, datos, datetime(2026, 10, 26, 13, tzinfo=UTC), minutos=30)

    movido = _reprogramar(uow, datos, pasado.id, inicio=datetime(2026, 10, 27, 13, tzinfo=UTC))

    assert movido.inicio == datetime(2026, 10, 27, 13, tzinfo=UTC)


def test_rep5a_la_entrada_se_valida_antes_que_el_estado(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    _poner_estado(sesion, ana.id, "cancelado_paciente")

    with pytest.raises(EntradaInvalida):
        _reprogramar(uow, datos, ana.id, duracion_minutos=42)


@pytest.mark.parametrize(("inicio", "duracion"), [(None, None), (a_las(13), 30)])
def test_rep5b_un_terminal_sin_cambios_responde_sin_evento(sesion, uow, inicio, duracion):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    _poner_estado(sesion, ana.id, "atendido")

    resultado = _reprogramar(uow, datos, ana.id, inicio=inicio, duracion_minutos=duracion)

    assert resultado.estado.value == "atendido"
    assert _tipos(uow, ana.id) == ["creado"]


def test_rep5b_un_terminal_con_un_cambio_da_rn_ag_18(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    _poner_estado(sesion, ana.id, "atendido")

    with pytest.raises(TurnoNoReprogramable):
        _reprogramar(uow, datos, ana.id, inicio=a_las(17))
