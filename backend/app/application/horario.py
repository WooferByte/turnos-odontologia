"""Casos de uso del horario recurrente (US-002; RN-AG-16, RN-GL-04). Sin ``commit()`` ni SQL.

El consultorio es el del usuario que hace la petición: un profesional de otro consultorio cuenta
como inexistente (404), igual que un id que no existe (design H5).
"""
from collections.abc import Sequence
from dataclasses import dataclass

from app.application.puertos import UnidadDeTrabajo
from app.domain.agenda.horario import Franja, validar_franjas
from app.domain.agenda.profesionales import DatosProfesional
from app.domain.errors import EntradaInvalida, ProfesionalNoEncontrado


@dataclass(frozen=True)
class HorarioDelProfesional:
    profesional_id: int
    zona_horaria: str
    franjas: Sequence[Franja]


def _consultorio_del_usuario(usuario_id: int, uow: UnidadDeTrabajo) -> int:
    return uow.usuarios.obtener(usuario_id).consultorio_id


def _profesional_del_consultorio(
    profesional_id: int, consultorio_id: int, uow: UnidadDeTrabajo
) -> DatosProfesional:
    profesional = uow.horario.profesional(profesional_id)
    if profesional is None or profesional.consultorio_id != consultorio_id:
        raise ProfesionalNoEncontrado(profesional_id)
    return profesional


def listar_profesionales(usuario_id: int, uow: UnidadDeTrabajo) -> Sequence[DatosProfesional]:
    """Los del consultorio, activos e inactivos, por ``id`` (D260)."""
    with uow:
        return uow.horario.profesionales_del_consultorio(_consultorio_del_usuario(usuario_id, uow))


def obtener_horario(profesional_id: int, usuario_id: int, uow: UnidadDeTrabajo) -> HorarioDelProfesional:
    with uow:
        consultorio_id = _consultorio_del_usuario(usuario_id, uow)
        profesional = _profesional_del_consultorio(profesional_id, consultorio_id, uow)
        return HorarioDelProfesional(
            profesional_id=profesional.id,
            zona_horaria=uow.agenda.zona_horaria(consultorio_id),
            franjas=uow.horario.franjas_de(profesional.id),
        )


def reemplazar_horario(
    profesional_id: int, franjas: Sequence[Franja], usuario_id: int, uow: UnidadDeTrabajo
) -> HorarioDelProfesional:
    """Valida el cuerpo (RN-AG-16, toda junta), después busca al profesional (404) y reemplaza.

    No toca ni informa los turnos existentes (D261); el horario de un inactivo se edita (D262).
    """
    errores = validar_franjas(franjas)
    if errores:
        raise EntradaInvalida(errores)
    with uow:
        consultorio_id = _consultorio_del_usuario(usuario_id, uow)
        profesional = _profesional_del_consultorio(profesional_id, consultorio_id, uow)
        uow.horario.reemplazar(profesional.id, franjas)
        return HorarioDelProfesional(
            profesional_id=profesional.id,
            zona_horaria=uow.agenda.zona_horaria(consultorio_id),
            franjas=uow.horario.franjas_de(profesional.id),
        )
