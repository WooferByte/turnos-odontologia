"""Fábricas de datos ficticios para los tests (D19, RN-PR-01).

Cada función guarda, hace ``commit()`` y devuelve el modelo con su ``id``.
"""
from datetime import datetime, timedelta
from itertools import count

from sqlalchemy.orm import Session

from app.infrastructure.db.modelos import (
    ConsultorioModelo,
    EventoTurnoModelo,
    PacienteModelo,
    PrestacionModelo,
    ProfesionalModelo,
    SillonModelo,
    TurnoModelo,
)
from tests.conftest import RELOJ_FIJO

_secuencia = count(1)


def _guardar(sesion: Session, modelo):
    sesion.add(modelo)
    sesion.commit()
    return modelo


def un_consultorio(sesion: Session, **kw) -> ConsultorioModelo:
    datos = {
        "nombre": "Consultorio de Prueba",
        "slug": f"consultorio-prueba-{next(_secuencia)}",
        "zona_horaria": "America/Argentina/Buenos_Aires",
    }
    return _guardar(sesion, ConsultorioModelo(**{**datos, **kw}))


def un_profesional(sesion: Session, consultorio: ConsultorioModelo, **kw) -> ProfesionalModelo:
    datos = {"nombre": "Profesional de Prueba", "activo": True}
    return _guardar(sesion, ProfesionalModelo(consultorio_id=consultorio.id, **{**datos, **kw}))


def un_sillon(sesion: Session, consultorio: ConsultorioModelo, **kw) -> SillonModelo:
    datos = {"nombre": "Sillón de Prueba", "activo": True}
    return _guardar(sesion, SillonModelo(consultorio_id=consultorio.id, **{**datos, **kw}))


def una_prestacion(sesion: Session, consultorio: ConsultorioModelo, **kw) -> PrestacionModelo:
    datos = {
        "nombre": f"Prestación de Prueba {next(_secuencia)}",
        "duracion_minutos": 30,
        "activa": True,
    }
    return _guardar(sesion, PrestacionModelo(consultorio_id=consultorio.id, **{**datos, **kw}))


def un_paciente(sesion: Session, consultorio: ConsultorioModelo, **kw) -> PacienteModelo:
    datos = {"nombre": "Paciente", "apellido": "De Prueba", "telefono_whatsapp": "+5491155550100"}
    return _guardar(sesion, PacienteModelo(consultorio_id=consultorio.id, **{**datos, **kw}))


def un_turno(
    sesion: Session,
    *,
    paciente: PacienteModelo,
    profesional: ProfesionalModelo,
    sillon: SillonModelo,
    prestacion: PrestacionModelo,
    inicio: datetime,
    estado: str = "reservado",
    **kw,
) -> TurnoModelo:
    datos = {
        "consultorio_id": profesional.consultorio_id,
        "duracion_minutos": prestacion.duracion_minutos,
        "fin": inicio + timedelta(minutes=prestacion.duracion_minutos),
        "creado_en": RELOJ_FIJO,
    }
    return _guardar(
        sesion,
        TurnoModelo(
            paciente_id=paciente.id,
            profesional_id=profesional.id,
            sillon_id=sillon.id,
            prestacion_id=prestacion.id,
            inicio=inicio,
            estado=estado,
            **{**datos, **kw},
        ),
    )


def un_evento(sesion: Session, turno: TurnoModelo, **kw) -> EventoTurnoModelo:
    datos = {
        "tipo": "creado",
        "actor_tipo": "usuario",
        "actor_id": None,
        "ocurrido_en": RELOJ_FIJO,
        "antes": None,
        "despues": {"estado": turno.estado},
        "motivo": None,
    }
    return _guardar(sesion, EventoTurnoModelo(turno_id=turno.id, **{**datos, **kw}))
