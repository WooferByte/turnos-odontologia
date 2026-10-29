"""Caso de uso: crear un turno (E1). No hace ``commit()`` ni arma SQL: eso es de la unidad de trabajo."""
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.application.puertos import SolapamientoEnLaBase, UnidadDeTrabajo
from app.domain.agenda.bloqueos import exigir_sin_bloqueos
from app.domain.agenda.horario import exigir_dentro_del_horario
from app.domain.agenda.intervalo import Intervalo
from app.domain.agenda.recursos import Paciente, Prestacion, Profesional, Sillon
from app.domain.agenda.solapamiento import detectar_conflictos
from app.domain.errors import (
    EntradaInvalida,
    ErrorDeDominio,
    ErrorDeSolapamiento,
    FechaNoUTC,
    RecursoNoEncontrado,
    ReferenciaInvalida,
)
from app.domain.tiempo import Reloj, exigir_utc, utc_now
from app.domain.turnos.estados import EstadoTurno
from app.domain.turnos.eventos import Actor, evento_creado
from app.domain.turnos.turno import Turno


INTENTOS_ANTE_CARRERA = 3  # design I8

Motivo = Literal["inexistente", "inactivo", "ninguno_activo", "varios_activos"]


@dataclass(frozen=True)
class CrearTurnoComando:
    paciente_id: int
    prestacion_id: int
    inicio: datetime
    profesional_id: int | None = None
    sillon_id: int | None = None


def _motivo_sin_unico_activo(cantidad_de_activos: int) -> Motivo:
    """Por qué un recurso omitido no se pudo resolver por defecto (RN-AG-14, D9)."""
    return "ninguno_activo" if cantidad_de_activos == 0 else "varios_activos"


def _es_de_otro_consultorio(
    recurso: Paciente | Prestacion | Sillon, consultorio_id: int | None
) -> bool:
    """Un recurso de otro consultorio cuenta como inexistente (D126); sin C no se puede decir."""
    return consultorio_id is not None and recurso.consultorio_id != consultorio_id


def _validar_entrada(
    comando: CrearTurnoComando, uow: UnidadDeTrabajo
) -> tuple[Profesional, Prestacion, Sillon]:
    """Validación de entrada, toda junta (D6, D10): la fecha y las referencias, siempre las dos.

    Devuelve los recursos ya resueltos (también los que se omitieron, RN-AG-14) o levanta un
    único ``EntradaInvalida`` con todo lo que falló.
    """
    errores: list[ErrorDeDominio] = []
    try:
        exigir_utc(comando.inicio, "inicio")
    except FechaNoUTC as error:
        errores.append(error)
    referencias: list[ReferenciaInvalida] = []
    paciente = uow.agenda.paciente(comando.paciente_id)
    # Motivo con el que se informa un profesional que no se resolvió; None = no se informa.
    motivo_profesional: Motivo | None = "inexistente"
    if comando.profesional_id is None:  # RN-AG-14: el único activo del consultorio del paciente
        profesional = None
        motivo_profesional = None  # sin paciente no hay consultorio donde buscarlo (D10)
        if paciente is not None:
            activos = uow.agenda.profesionales_activos(paciente.consultorio_id)
            profesional = activos[0] if len(activos) == 1 else None
            motivo_profesional = _motivo_sin_unico_activo(len(activos))
    else:
        profesional = uow.agenda.profesional(comando.profesional_id)
    # Consultorio del turno (C, D10): el del profesional; desconocido (None) si no se resolvió.
    consultorio_id = profesional.consultorio_id if profesional and profesional.activo else None
    prestacion = uow.agenda.prestacion(comando.prestacion_id)
    if prestacion is None or _es_de_otro_consultorio(prestacion, consultorio_id):
        referencias.append(ReferenciaInvalida("prestacion", comando.prestacion_id, "inexistente"))
    elif not prestacion.activa:
        referencias.append(ReferenciaInvalida("prestacion", prestacion.id, "inactivo"))
    if paciente is None or _es_de_otro_consultorio(paciente, consultorio_id):
        referencias.append(ReferenciaInvalida("paciente", comando.paciente_id, "inexistente"))
    if profesional is None:
        if motivo_profesional is not None:
            referencias.append(
                ReferenciaInvalida("profesional", comando.profesional_id, motivo_profesional)
            )
    elif not profesional.activo:
        referencias.append(ReferenciaInvalida("profesional", profesional.id, "inactivo"))
    motivo_sillon: Motivo | None = "inexistente"
    if comando.sillon_id is None:  # RN-AG-14: el único activo del consultorio del turno
        sillon = None
        motivo_sillon = None  # sin consultorio del turno no se puede buscar (D10)
        if consultorio_id is not None:
            activos_sillon = uow.agenda.sillones_activos(consultorio_id)
            sillon = activos_sillon[0] if len(activos_sillon) == 1 else None
            motivo_sillon = _motivo_sin_unico_activo(len(activos_sillon))
    else:
        sillon = uow.agenda.sillon(comando.sillon_id)
    if sillon is None or _es_de_otro_consultorio(sillon, consultorio_id):
        if motivo_sillon is not None:
            referencias.append(ReferenciaInvalida("sillon", comando.sillon_id, motivo_sillon))
    elif not sillon.activo:
        referencias.append(ReferenciaInvalida("sillon", sillon.id, "inactivo"))
    if referencias:
        errores.append(RecursoNoEncontrado(tuple(referencias)))
    if errores:
        raise EntradaInvalida(tuple(errores))
    return profesional, prestacion, sillon


def evaluar_horario_de_un_turno(
    uow: UnidadDeTrabajo,
    *,
    consultorio_id: int,
    profesional_id: int,
    sillon_id: int,
    inicio: datetime,
    duracion_minutos: int,
    excluir_turno_id: int | None = None,
) -> Intervalo:
    """Las reglas del horario de un turno, en su orden: RN-AG-10d, RN-AG-04, RN-AG-04b y el solapamiento.

    Las comparten el alta y la reprogramación (design M5). ``excluir_turno_id`` es el turno que se
    mueve: no choca consigo mismo (RN-AG-10b). Devuelve el intervalo ya validado y con los bloqueos
    de fila del profesional y del sillón tomados.
    """
    zona = uow.agenda.zona_horaria(consultorio_id)
    intervalo = Intervalo.para_turno(inicio, duracion_minutos, zona)
    # RN-AG-04, después de RN-AG-10d y antes del solapamiento (07 Flujo 1); sin tomar bloqueos de fila.
    exigir_dentro_del_horario(intervalo, uow.horario.franjas_de(profesional_id), zona)
    # RN-AG-04b, después del horario y antes del solapamiento (D280); tampoco toma bloqueos de fila (B10).
    bloqueos = uow.bloqueos.que_intersecan(consultorio_id, profesional_id, sillon_id, intervalo)
    exigir_sin_bloqueos(intervalo, profesional_id, sillon_id, consultorio_id, bloqueos)
    # Serializa por recurso: la escritura que llega segunda espera acá y, al seguir, lee el
    # turno que la primera ya confirmó (E11, design I8).
    uow.agenda.bloquear_recursos(profesional_id, sillon_id)
    ocupados = uow.agenda.ocupados_en_el_intervalo(profesional_id, sillon_id, intervalo)
    conflictos = detectar_conflictos(
        intervalo,
        profesional_id,
        ocupados.del_profesional,
        sillon_id,
        ocupados.del_sillon,
        excluir_turno_id=excluir_turno_id,
    )
    if conflictos:
        raise ErrorDeSolapamiento(conflictos)
    return intervalo


def _intentar_crear_turno(
    comando: CrearTurnoComando, uow: UnidadDeTrabajo, reloj: Reloj, actor: Actor, creado_por: int
) -> Turno:
    with uow:
        profesional, prestacion, sillon = _validar_entrada(comando, uow)
        intervalo = evaluar_horario_de_un_turno(
            uow,
            consultorio_id=profesional.consultorio_id,
            profesional_id=profesional.id,
            sillon_id=sillon.id,
            inicio=comando.inicio,
            duracion_minutos=prestacion.duracion_minutos,
        )
        turno = uow.agenda.agregar(
            Turno(
                consultorio_id=profesional.consultorio_id,
                paciente_id=comando.paciente_id,
                profesional_id=profesional.id,
                sillon_id=sillon.id,
                prestacion_id=prestacion.id,
                inicio=intervalo.inicio,
                fin=intervalo.fin,
                duracion_minutos=prestacion.duracion_minutos,
                estado=EstadoTurno.RESERVADO,
                creado_en=reloj(),
                creado_por=creado_por,
            )
        )
        # Mismo ``with uow:``: el turno y su evento ``creado`` se confirman juntos o ninguno (E9).
        uow.historial.registrar(evento_creado(turno, actor))
        return turno


def crear_turno(
    comando: CrearTurnoComando,
    uow: UnidadDeTrabajo,
    reloj: Reloj = utc_now,
    *,
    actor: Actor,
    creado_por: int,
) -> Turno:
    """Crea el turno a nombre de ``actor`` y ``creado_por`` (obligatorios, D210); ante una carrera (E11) reevalúa.

    Si la base lo rechaza por una carrera, reevalúa con el dominio.

    Antes de leer los ocupados toma el bloqueo del profesional y del sillón, así que la segunda
    reserva del mismo recurso espera y ya ve el turno confirmado: el reintento es la red para
    escrituras que no pasan por acá. El ganador ya confirmó cuando la base devuelve la violación
    (23P01), así que el intento siguiente lo encuentra y levanta el ``ErrorDeSolapamiento`` de
    siempre (design I8). Si todos los intentos chocan, ``SolapamientoEnLaBase`` sube sin traducir:
    dominio y base no coinciden.
    """
    for _ in range(INTENTOS_ANTE_CARRERA - 1):
        try:
            return _intentar_crear_turno(comando, uow, reloj, actor, creado_por)
        except SolapamientoEnLaBase:
            continue  # otra transacción ganó el hueco: ahora el dominio ya la ve
    return _intentar_crear_turno(comando, uow, reloj, actor, creado_por)
