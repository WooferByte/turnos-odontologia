"""Casos de uso de los bloqueos puntuales (US-003; RN-AG-17, RN-GL-01, RN-GL-04). Sin ``commit()`` ni SQL.

El consultorio es el del usuario que hace la petición (D270): un profesional, un sillón o un bloqueo de
otro consultorio cuenta como inexistente (design B5, B12). Crear un bloqueo no cancela ni modifica
ningún turno: solo informa los activos que quedan adentro (D83).
"""
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from app.application.puertos import UnidadDeTrabajo
from app.domain.agenda.bloqueos import DatosBloqueo, turnos_afectados, validar_fechas_del_bloqueo
from app.domain.errors import (
    BloqueoInvertido,
    BloqueoNoEncontrado,
    EntradaInvalida,
    ErrorDeDominio,
    FechaNoUTC,
    RecursoNoEncontrado,
    ReferenciaInvalida,
)
from app.domain.tiempo import exigir_utc
from app.domain.turnos.turno import Turno


@dataclass(frozen=True)
class CrearBloqueoComando:
    inicio: datetime
    fin: datetime
    motivo: str
    profesional_id: int | None = None
    sillon_id: int | None = None


@dataclass(frozen=True)
class BloqueoCreado:
    bloqueo: DatosBloqueo
    turnos_afectados: Sequence[Turno]


@dataclass(frozen=True)
class BloqueosDelConsultorio:
    zona_horaria: str
    bloqueos: Sequence[DatosBloqueo]


def _consultorio_del_usuario(usuario_id: int, uow: UnidadDeTrabajo) -> int:
    return uow.usuarios.obtener(usuario_id).consultorio_id


def _validar_entrada(comando: CrearBloqueoComando, consultorio_id: int, uow: UnidadDeTrabajo) -> None:
    """Validación de entrada, toda junta (RN-GL-02): fechas UTC, referencias y, con las dos fechas válidas, RN-AG-17."""
    errores: list[ErrorDeDominio] = []
    fechas_validas = True
    for campo, valor in (("inicio", comando.inicio), ("fin", comando.fin)):
        try:
            exigir_utc(valor, campo)
        except FechaNoUTC as error:
            errores.append(error)
            fechas_validas = False
    referencias: list[ReferenciaInvalida] = []
    if comando.profesional_id is not None:
        profesional = uow.agenda.profesional(comando.profesional_id)
        if profesional is None or profesional.consultorio_id != consultorio_id:
            referencias.append(ReferenciaInvalida("profesional", comando.profesional_id, "inexistente"))
        elif not profesional.activo:
            referencias.append(ReferenciaInvalida("profesional", profesional.id, "inactivo"))
    if comando.sillon_id is not None:
        sillon = uow.agenda.sillon(comando.sillon_id)
        if sillon is None or sillon.consultorio_id != consultorio_id:
            referencias.append(ReferenciaInvalida("sillon", comando.sillon_id, "inexistente"))
        elif not sillon.activo:
            referencias.append(ReferenciaInvalida("sillon", sillon.id, "inactivo"))
    if referencias:
        errores.append(RecursoNoEncontrado(tuple(referencias)))
    if fechas_validas:
        try:
            validar_fechas_del_bloqueo(comando.inicio, comando.fin)
        except BloqueoInvertido as error:
            errores.append(error)
    if errores:
        raise EntradaInvalida(tuple(errores))


def listar_bloqueos(usuario_id: int, uow: UnidadDeTrabajo) -> BloqueosDelConsultorio:
    """Todos los del consultorio, pasados y futuros, por ``(inicio, id)`` (D279)."""
    with uow:
        consultorio_id = _consultorio_del_usuario(usuario_id, uow)
        return BloqueosDelConsultorio(
            zona_horaria=uow.agenda.zona_horaria(consultorio_id),
            bloqueos=uow.bloqueos.del_consultorio(consultorio_id),
        )


def crear_bloqueo(comando: CrearBloqueoComando, usuario_id: int, uow: UnidadDeTrabajo) -> BloqueoCreado:
    with uow:
        consultorio_id = _consultorio_del_usuario(usuario_id, uow)
        _validar_entrada(comando, consultorio_id, uow)
        guardado = uow.bloqueos.agregar(
            DatosBloqueo(
                id=None,
                consultorio_id=consultorio_id,
                profesional_id=comando.profesional_id,
                sillon_id=comando.sillon_id,
                inicio=comando.inicio,
                fin=comando.fin,
                motivo=comando.motivo,
                creado_por=usuario_id,
            )
        )
        candidatos = uow.agenda.turnos_activos_que_intersecan(guardado)
        return BloqueoCreado(guardado, turnos_afectados(guardado, candidatos))


def eliminar_bloqueo(bloqueo_id: int, usuario_id: int, uow: UnidadDeTrabajo) -> None:
    """Borrado físico (D278); un bloqueo inexistente o de otro consultorio es ``404`` con RN-GL-04."""
    with uow:
        consultorio_id = _consultorio_del_usuario(usuario_id, uow)
        bloqueo = uow.bloqueos.obtener(bloqueo_id)
        if bloqueo is None or bloqueo.consultorio_id != consultorio_id:
            raise BloqueoNoEncontrado(bloqueo_id)
        uow.bloqueos.eliminar(bloqueo_id)
