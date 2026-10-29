"""Caso de uso ``cancelar_turno`` con repositorio real sobre SQLite en memoria (C-17; US-013, RN-AG-12)."""
from datetime import datetime

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.exc import DBAPIError

from app.application.cancelar_turno import CancelarTurnoComando, cancelar_turno
from app.application.crear_turno import CrearTurnoComando, crear_turno
from app.application.historial import consultar_historial
from app.application.reprogramar_turno import ReprogramarTurnoComando, reprogramar_turno
from app.domain.errors import TransicionInvalida, TurnoNoEncontrado
from app.domain.turnos.estados import EstadoTurno
from app.domain.turnos.eventos import Actor, ActorTipo, TipoEvento
from app.infrastructure.db.modelos import EventoTurnoModelo, TurnoModelo
from tests.conftest import RELOJ_FIJO, a_las, reloj_fijo
from tests.factories import (
    ACTOR_DE_PRUEBA,
    ID_DE_USUARIO_DE_PRUEBA,
    un_consultorio,
    un_paciente,
    un_profesional,
    una_prestacion,
    un_sillon,
    un_turno,
    un_usuario,
)

RECEPCIONISTA = Actor(ActorTipo.USUARIO, "2")
TERMINALES = ["cancelado_paciente", "cancelado_profesional", "vencido", "atendido", "ausente"]
ACTIVOS = ["pendiente_aprobacion", "pendiente_sena", "reservado", "confirmado"]
CANCELACIONES = ["cancelado_paciente", "cancelado_profesional"]


def _escenario(sesion, duracion_minutos: int = 30) -> dict:
    consultorio = un_consultorio(sesion)
    return {
        "consultorio": consultorio,
        "usuario": un_usuario(sesion, consultorio),
        "paciente": un_paciente(sesion, consultorio),
        "profesional": un_profesional(sesion, consultorio),
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


def _cancelar(uow, datos: dict, turno_id: int, estado: str = "cancelado_paciente"):
    return cancelar_turno(
        CancelarTurnoComando(turno_id, EstadoTurno(estado)),
        datos["usuario"].id,
        uow,
        reloj_fijo,
        actor=RECEPCIONISTA,
    )


def test_can1a_cancelar_cambia_solo_el_estado(sesion, uow):
    datos = _escenario(sesion)
    original = _crear(uow, datos, a_las(13))

    cancelado = _cancelar(uow, datos, original.id, "cancelado_paciente")

    assert cancelado.id == original.id
    assert cancelado.estado.value == "cancelado_paciente"
    assert (cancelado.inicio, cancelado.fin, cancelado.duracion_minutos) == (a_las(13), a_las(13, 30), 30)
    assert cancelado.paciente_id == original.paciente_id
    assert cancelado.prestacion_id == original.prestacion_id
    assert cancelado.profesional_id == original.profesional_id
    assert cancelado.sillon_id == original.sillon_id
    assert cancelado.creado_en == original.creado_en
    assert sesion.scalar(select(func.count()).select_from(TurnoModelo)) == 1


def test_can2a_cancelar_registra_el_evento(sesion, uow):
    datos = _escenario(sesion)
    original = _crear(uow, datos, a_las(13))

    _cancelar(uow, datos, original.id, "cancelado_profesional")

    eventos = consultar_historial(original.id, uow)
    assert [e.tipo for e in eventos] == [TipoEvento.CREADO, TipoEvento.CANCELADO]
    cancelado = eventos[1]
    assert cancelado.actor_id == "2"
    assert cancelado.ocurrido_en == RELOJ_FIJO
    assert cancelado.antes == {"estado": "reservado"}
    assert cancelado.despues == {"estado": "cancelado_profesional"}
    assert cancelado.motivo is None


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


def _tipos(uow, turno_id: int) -> list[str]:
    return [e.tipo.value for e in consultar_historial(turno_id, uow)]


def _estado_de(uow, turno_id: int) -> str:
    with uow:
        return uow.agenda.turno_para_cambiar(turno_id).estado.value


@pytest.mark.parametrize("estado", CANCELACIONES)
def test_can1a_se_cancela_con_los_dos_valores(sesion, uow, estado):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))

    cancelado = _cancelar(uow, datos, ana.id, estado)

    assert cancelado.estado.value == estado
    assert _estado_de(uow, ana.id) == estado


def test_can1b_el_hueco_queda_libre_para_crear(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    _cancelar(uow, datos, ana.id, "cancelado_profesional")

    nuevo = _crear(uow, datos, a_las(13))

    assert nuevo.id != ana.id
    assert (nuevo.inicio, nuevo.estado.value) == (a_las(13), "reservado")


def test_can1b_el_hueco_queda_libre_para_reprogramar(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    bruno = _de_otro(sesion, datos, a_las(18), minutos=30)
    _cancelar(uow, datos, ana.id, "cancelado_paciente")

    movido = reprogramar_turno(
        ReprogramarTurnoComando(bruno.id, inicio=a_las(13)),
        datos["usuario"].id,
        uow,
        reloj_fijo,
        actor=RECEPCIONISTA,
    )

    assert (movido.id, movido.inicio) == (bruno.id, a_las(13))


@pytest.mark.parametrize("destino", CANCELACIONES)
@pytest.mark.parametrize("estado", ACTIVOS)
def test_can1b_se_cancela_desde_cada_estado_activo(sesion, uow, estado, destino):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    _poner_estado(sesion, ana.id, estado)

    cancelado = _cancelar(uow, datos, ana.id, destino)

    assert cancelado.estado.value == destino
    assert _tipos(uow, ana.id) == ["creado", "cancelado"]


@pytest.mark.parametrize(
    ("inicio", "estado"),
    [
        ("2026-10-26T13:00:00+00:00", "reservado"),  # ya pasado según el reloj
        ("2026-10-29T12:05:00+00:00", "confirmado"),  # empieza en cinco minutos
    ],
)
def test_can1b_se_cancela_en_cualquier_momento(sesion, uow, inicio, estado):
    datos = _escenario(sesion)
    ana = _de_otro(sesion, datos, datetime.fromisoformat(inicio), estado=estado, minutos=30)

    cancelado = _cancelar(uow, datos, ana.id, "cancelado_paciente")

    assert cancelado.estado.value == "cancelado_paciente"


@pytest.mark.parametrize("pedido", CANCELACIONES)
@pytest.mark.parametrize("estado", TERMINALES)
def test_can1c_un_terminal_se_rechaza_sin_cambios_ni_eventos(sesion, uow, estado, pedido):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    _poner_estado(sesion, ana.id, estado)

    with pytest.raises(TransicionInvalida) as error:
        _cancelar(uow, datos, ana.id, pedido)

    assert error.value.codigos == ["RN-AG-12"]
    assert _estado_de(uow, ana.id) == estado
    assert _tipos(uow, ana.id) == ["creado"]


def test_can1c_la_misma_cancelacion_repetida_da_rn_ag_12_y_deja_un_solo_evento(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    _cancelar(uow, datos, ana.id, "cancelado_paciente")

    for pedido in ("cancelado_paciente", "cancelado_profesional"):
        with pytest.raises(TransicionInvalida):
            _cancelar(uow, datos, ana.id, pedido)

    assert _estado_de(uow, ana.id) == "cancelado_paciente"
    assert _tipos(uow, ana.id) == ["creado", "cancelado"]


def test_can1c_un_turno_de_otro_consultorio_es_inexistente(sesion, uow):
    datos = _escenario(sesion)
    ajeno = _escenario(sesion)
    del_otro = _de_otro(sesion, ajeno, a_las(13))

    for turno_id in (999, del_otro.id):
        with pytest.raises(TurnoNoEncontrado):
            _cancelar(uow, datos, turno_id)

    assert sesion.scalar(select(TurnoModelo.estado).where(TurnoModelo.id == del_otro.id)) == "reservado"


def test_can2b_un_rechazo_no_registra_eventos(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    _poner_estado(sesion, ana.id, "atendido")

    with pytest.raises(TransicionInvalida):
        _cancelar(uow, datos, ana.id)

    assert _tipos(uow, ana.id) == ["creado"]


def test_can2c_si_el_evento_falla_el_turno_no_se_cancela(sesion, engine, fabrica_sesiones, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    with engine.begin() as conexion:  # falla real de la base, sin dobles (como REP-2b)
        conexion.exec_driver_sql(
            "CREATE TRIGGER evento_turno_falla BEFORE INSERT ON evento_turno "
            "BEGIN SELECT RAISE(ABORT, 'falla de prueba al registrar el evento'); END"
        )

    with pytest.raises(DBAPIError, match="falla de prueba al registrar el evento"):
        _cancelar(uow, datos, ana.id)

    with engine.begin() as conexion:
        conexion.exec_driver_sql("DROP TRIGGER evento_turno_falla")
    assert _estado_de(uow, ana.id) == "reservado"
    with fabrica_sesiones() as otra:
        assert otra.scalar(select(func.count()).select_from(EventoTurnoModelo)) == 1
    assert _tipos(uow, ana.id) == ["creado"]
