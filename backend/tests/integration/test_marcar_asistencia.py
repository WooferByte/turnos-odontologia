"""Caso de uso ``marcar_asistencia`` con repositorio real sobre SQLite en memoria (C-18; US-014, RN-AG-13)."""
from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.exc import DBAPIError

from app.application.crear_turno import CrearTurnoComando, crear_turno
from app.application.historial import consultar_historial
from app.application.marcar_asistencia import MarcarAsistenciaComando, marcar_asistencia
from app.domain.errors import MarcadoAntesDelInicio, TransicionInvalida, TurnoNoEncontrado
from app.domain.turnos.estados import EstadoTurno
from app.domain.turnos.eventos import Actor, ActorTipo, TipoEvento
from app.infrastructure.db.modelos import (
    EventoTurnoModelo,
    PacienteModelo,
    ProfesionalModelo,
    PrestacionModelo,
    SillonModelo,
    TurnoModelo,
)
from tests.conftest import a_las, reloj_fijo
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

AHORA = datetime(2026, 11, 2, 13, 10, tzinfo=UTC)  # 10 minutos después de a_las(13)
RECEPCIONISTA = Actor(ActorTipo.USUARIO, "2")
TERMINALES = ["cancelado_paciente", "cancelado_profesional", "vencido", "atendido", "ausente"]
NO_SE_MARCAN = ["pendiente_aprobacion", "pendiente_sena", *TERMINALES]
MARCABLES = ["reservado", "confirmado"]
MARCADOS = ["atendido", "ausente"]


def _reloj(ahora: datetime = AHORA):
    return lambda: ahora


def _escenario(sesion, duracion_minutos: int = 30) -> dict:
    consultorio = un_consultorio(sesion)
    return {
        "consultorio": consultorio,
        "usuario": un_usuario(sesion, consultorio),
        "paciente": un_paciente(sesion, consultorio, nombre="Ana"),
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


def _marcar(uow, datos: dict, turno_id: int, estado: str = "atendido", ahora: datetime = AHORA):
    return marcar_asistencia(
        MarcarAsistenciaComando(turno_id, EstadoTurno(estado)),
        datos["usuario"].id,
        uow,
        _reloj(ahora),
        actor=RECEPCIONISTA,
    )


def _poner_estado(sesion, turno_id: int, estado: str) -> None:
    sesion.execute(update(TurnoModelo).where(TurnoModelo.id == turno_id).values(estado=estado))
    sesion.commit()


def _de_otro(sesion, datos, inicio, estado="reservado", minutos=45, paciente=None, **nombres):
    """Un turno guardado directo (sin reglas) del mismo profesional y sillón, para otro paciente."""
    paciente = paciente or un_paciente(sesion, datos["consultorio"], nombre="Bruno", apellido="Ficticio")
    prestacion = una_prestacion(sesion, datos["consultorio"], duracion_minutos=minutos)
    return un_turno(
        sesion,
        paciente=paciente,
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


def _es_nuevo(sesion, paciente_id: int) -> bool:
    sesion.expire_all()
    return sesion.scalar(select(PacienteModelo.es_nuevo).where(PacienteModelo.id == paciente_id))


def test_asi1a_marcar_cambia_solo_el_estado(sesion, uow):
    datos = _escenario(sesion)
    original = _crear(uow, datos, a_las(13))

    marcado = _marcar(uow, datos, original.id, "atendido")

    assert marcado.id == original.id
    assert marcado.estado.value == "atendido"
    assert (marcado.inicio, marcado.fin, marcado.duracion_minutos) == (a_las(13), a_las(13, 30), 30)
    assert marcado.paciente_id == original.paciente_id
    assert marcado.prestacion_id == original.prestacion_id
    assert marcado.profesional_id == original.profesional_id
    assert marcado.sillon_id == original.sillon_id
    assert marcado.creado_en == original.creado_en
    assert sesion.scalar(select(func.count()).select_from(TurnoModelo)) == 1


def test_asi2a_marcar_registra_el_evento(sesion, uow):
    datos = _escenario(sesion)
    original = _crear(uow, datos, a_las(13))

    _marcar(uow, datos, original.id, "atendido")

    eventos = consultar_historial(original.id, uow)
    assert [e.tipo for e in eventos] == [TipoEvento.CREADO, TipoEvento.ESTADO_CAMBIADO]
    cambio = eventos[1]
    assert cambio.actor_id == "2"
    assert cambio.ocurrido_en == AHORA
    assert cambio.antes == {"estado": "reservado"}
    assert cambio.despues == {"estado": "atendido"}
    assert cambio.motivo is None


def test_asi3a_el_primer_atendido_deja_de_ser_nuevo(sesion, uow):
    datos = _escenario(sesion)
    bruno = un_paciente(sesion, datos["consultorio"], nombre="Bruno")
    ana = _crear(uow, datos, a_las(13))
    _crear(uow, datos, a_las(14), paciente=bruno)

    _marcar(uow, datos, ana.id, "atendido")

    assert _es_nuevo(sesion, datos["paciente"].id) is False
    assert _es_nuevo(sesion, bruno.id) is True


@pytest.mark.parametrize("estado", MARCADOS)
def test_asi1a_se_marca_con_los_dos_valores(sesion, uow, estado):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))

    marcado = _marcar(uow, datos, ana.id, estado)

    assert marcado.estado.value == estado
    assert _estado_de(uow, ana.id) == estado


def test_asi1b_el_hueco_queda_libre_para_crear(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    _marcar(uow, datos, ana.id, "ausente")

    nuevo = _crear(uow, datos, a_las(13))

    assert nuevo.id != ana.id
    assert (nuevo.inicio, nuevo.estado.value) == (a_las(13), "reservado")


@pytest.mark.parametrize("destino", MARCADOS)
@pytest.mark.parametrize("estado", MARCABLES)
def test_asi1b_se_marca_desde_reservado_y_desde_confirmado(sesion, uow, estado, destino):
    datos = _escenario(sesion)
    ana = _de_otro(sesion, datos, a_las(13), estado=estado, minutos=30, paciente=datos["paciente"])

    marcado = _marcar(uow, datos, ana.id, destino)

    assert marcado.estado.value == destino
    assert _tipos(uow, ana.id) == ["estado_cambiado"]


def test_asi1b_ahora_igual_a_inicio(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))

    marcado = _marcar(uow, datos, ana.id, "atendido", ahora=a_las(13))

    assert marcado.estado.value == "atendido"


def test_asi1b_un_turno_de_dias_atras_se_marca(sesion, uow):
    datos = _escenario(sesion)
    ana = _de_otro(sesion, datos, datetime(2026, 10, 26, 13, 0, tzinfo=UTC), minutos=30, paciente=datos["paciente"])

    marcado = _marcar(uow, datos, ana.id, "ausente")

    assert marcado.estado.value == "ausente"


@pytest.mark.parametrize("pedido", MARCADOS)
@pytest.mark.parametrize("estado", NO_SE_MARCAN)
def test_asi1c_un_estado_que_no_se_marca_se_rechaza_sin_cambios_ni_eventos(sesion, uow, estado, pedido):
    datos = _escenario(sesion)
    carla = un_paciente(sesion, datos["consultorio"], nombre="Carla", apellido="Inventada", es_nuevo=False)
    carla_turno = _crear(uow, datos, a_las(13), paciente=carla)
    _crear(uow, datos, a_las(15))  # otro activo, en un horario distinto
    _poner_estado(sesion, carla_turno.id, estado)

    with pytest.raises(TransicionInvalida) as error:
        _marcar(uow, datos, carla_turno.id, pedido)

    assert error.value.codigos == ["RN-AG-12"]
    assert _estado_de(uow, carla_turno.id) == estado
    assert _tipos(uow, carla_turno.id) == ["creado"]
    assert _es_nuevo(sesion, carla.id) is False


def test_asi1c_el_mismo_marcado_repetido_y_el_contrario_dan_rn_ag_12_y_dejan_un_solo_evento(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    _marcar(uow, datos, ana.id, "atendido")

    for pedido in ("atendido", "ausente"):
        with pytest.raises(TransicionInvalida):
            _marcar(uow, datos, ana.id, pedido)

    assert _estado_de(uow, ana.id) == "atendido"
    assert _tipos(uow, ana.id) == ["creado", "estado_cambiado"]


def test_asi1c_un_turno_de_otro_consultorio_es_inexistente(sesion, uow):
    datos = _escenario(sesion)
    ajeno = _escenario(sesion)
    del_otro = _de_otro(sesion, ajeno, a_las(13))

    for turno_id in (999, del_otro.id):
        with pytest.raises(TurnoNoEncontrado):
            _marcar(uow, datos, turno_id)

    assert sesion.scalar(select(TurnoModelo.estado).where(TurnoModelo.id == del_otro.id)) == "reservado"
    assert _es_nuevo(sesion, del_otro.paciente_id) is True


def test_asi1f_un_turno_con_recursos_desactivados_despues_se_marca(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    for modelo, clave, campo in (
        (ProfesionalModelo, "profesional", "activo"),
        (SillonModelo, "sillon", "activo"),
        (PrestacionModelo, "prestacion", "activa"),
    ):
        sesion.execute(update(modelo).where(modelo.id == datos[clave].id).values(**{campo: False}))
    sesion.commit()

    marcado = _marcar(uow, datos, ana.id, "atendido")

    assert marcado.estado.value == "atendido"
    assert _tipos(uow, ana.id) == ["creado", "estado_cambiado"]
    assert _es_nuevo(sesion, datos["paciente"].id) is False


UN_SEGUNDO_ANTES = datetime(2026, 11, 2, 12, 59, 59, tzinfo=UTC)  # a_las(13) menos un segundo


@pytest.mark.parametrize("estado", MARCABLES)
def test_asi1d_antes_del_inicio_da_rn_ag_13(sesion, uow, estado):
    datos = _escenario(sesion)
    ana = _de_otro(sesion, datos, a_las(13), estado=estado, minutos=30, paciente=datos["paciente"])

    with pytest.raises(MarcadoAntesDelInicio) as error:
        _marcar(uow, datos, ana.id, "atendido", ahora=UN_SEGUNDO_ANTES)

    assert error.value.codigos == ["RN-AG-13"]
    assert _estado_de(uow, ana.id) == estado
    assert _tipos(uow, ana.id) == []
    assert _es_nuevo(sesion, datos["paciente"].id) is True


def test_asi1d_un_cancelado_futuro_da_rn_ag_12_y_no_rn_ag_13(sesion, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    _poner_estado(sesion, ana.id, "cancelado_paciente")

    with pytest.raises(TransicionInvalida):
        _marcar(uow, datos, ana.id, "atendido", ahora=UN_SEGUNDO_ANTES)


@pytest.mark.parametrize("causa", ["RN-AG-12", "RN-AG-13"])
def test_asi2b_un_rechazo_no_registra_eventos_ni_cambia_es_nuevo(sesion, uow, causa):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    ahora = AHORA
    if causa == "RN-AG-12":
        _poner_estado(sesion, ana.id, "ausente")
    else:
        ahora = UN_SEGUNDO_ANTES

    with pytest.raises((TransicionInvalida, MarcadoAntesDelInicio)) as error:
        _marcar(uow, datos, ana.id, "atendido", ahora=ahora)

    assert error.value.codigo == causa
    assert _tipos(uow, ana.id) == ["creado"]
    assert _es_nuevo(sesion, datos["paciente"].id) is True


def test_asi2c_si_el_evento_falla_ni_el_turno_ni_es_nuevo_cambian(sesion, engine, fabrica_sesiones, uow):
    datos = _escenario(sesion)
    ana = _crear(uow, datos, a_las(13))
    with engine.begin() as conexion:  # falla real de la base, sin dobles (como CAN-2c)
        conexion.exec_driver_sql(
            "CREATE TRIGGER evento_turno_falla BEFORE INSERT ON evento_turno "
            "BEGIN SELECT RAISE(ABORT, 'falla de prueba al registrar el evento'); END"
        )

    with pytest.raises(DBAPIError, match="falla de prueba al registrar el evento"):
        _marcar(uow, datos, ana.id, "atendido")

    with engine.begin() as conexion:
        conexion.exec_driver_sql("DROP TRIGGER evento_turno_falla")
    assert _estado_de(uow, ana.id) == "reservado"
    assert _tipos(uow, ana.id) == ["creado"]
    with fabrica_sesiones() as otra:
        assert otra.scalar(select(func.count()).select_from(EventoTurnoModelo)) == 1
        assert otra.scalar(select(PacienteModelo.es_nuevo).where(PacienteModelo.id == datos["paciente"].id)) is True


def test_asi3b_ausente_no_cambia_es_nuevo_y_el_segundo_atendido_la_deja_en_false(sesion, uow):
    datos = _escenario(sesion)
    ana_1 = _crear(uow, datos, a_las(13))
    ana_2 = _crear(uow, datos, a_las(14))
    _marcar(uow, datos, ana_1.id, "ausente", ahora=a_las(15))
    assert _es_nuevo(sesion, datos["paciente"].id) is True

    _marcar(uow, datos, ana_2.id, "atendido", ahora=a_las(15))

    assert _es_nuevo(sesion, datos["paciente"].id) is False


def test_asi3b_un_paciente_que_ya_no_era_nuevo_sigue_igual(sesion, uow):
    datos = _escenario(sesion)
    bruno = un_paciente(sesion, datos["consultorio"], nombre="Bruno", es_nuevo=False)
    _de_otro(sesion, datos, a_las(9), estado="atendido", minutos=30, paciente=bruno)
    actual = _crear(uow, datos, a_las(13), paciente=bruno)

    _marcar(uow, datos, actual.id, "atendido")

    assert _es_nuevo(sesion, bruno.id) is False
