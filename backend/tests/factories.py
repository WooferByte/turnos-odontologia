"""Fábricas de datos ficticios para los tests (D19, RN-PR-01).

Cada función guarda, hace ``commit()`` y devuelve el modelo con su ``id``.
"""
from collections.abc import Sequence
from datetime import date, datetime, time, timedelta
from itertools import count

from sqlalchemy.orm import Session

from app.domain.acceso.roles import Rol
from app.domain.agenda.horario import Franja
from app.domain.turnos.eventos import Actor, ActorTipo
from app.infrastructure.db.modelos import (
    BloqueoModelo,
    ConsultorioModelo,
    EventoTurnoModelo,
    FranjaHorariaModelo,
    PacienteModelo,
    PrestacionModelo,
    ProfesionalModelo,
    SillonModelo,
    TurnoModelo,
    UsuarioModelo,
    UsuarioRolModelo,
)
from app.infrastructure.seguridad.contrasenas import HasherBcrypt
from tests.conftest import RELOJ_FIJO

_secuencia = count(1)

# Quién crea los turnos en los tests de casos de uso (D210): un id de usuario ficticio, como texto en el evento.
ID_DE_USUARIO_DE_PRUEBA = 1
ACTOR_DE_PRUEBA = Actor(ActorTipo.USUARIO, str(ID_DE_USUARIO_DE_PRUEBA))


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


def franja(
    dia: int,
    desde: str,
    hasta: str,
    vigente_desde: date | None = None,
    vigente_hasta: date | None = None,
) -> Franja:
    """Franja ficticia: ``dia`` de 0 (lunes) a 6, horas ``HH:MM`` del consultorio."""
    return Franja(
        dia_semana=dia,
        hora_inicio=time.fromisoformat(desde),
        hora_fin=time.fromisoformat(hasta),
        vigente_desde=vigente_desde,
        vigente_hasta=vigente_hasta,
    )


# D263: sin pedir otra cosa, el profesional atiende todo el día, todos los días: así los tests
# que no hablan del horario no dependen de él. ``horario=()`` lo deja sin franjas.
HORARIO_DE_PRUEBA = tuple(franja(dia, "00:00", "23:59") for dia in range(7))


def un_profesional(
    sesion: Session,
    consultorio: ConsultorioModelo,
    horario: Sequence[Franja] = HORARIO_DE_PRUEBA,
    **kw,
) -> ProfesionalModelo:
    datos = {"nombre": "Profesional de Prueba", "activo": True}
    profesional = _guardar(sesion, ProfesionalModelo(consultorio_id=consultorio.id, **{**datos, **kw}))
    for f in horario:
        sesion.add(
            FranjaHorariaModelo(
                profesional_id=profesional.id,
                dia_semana=f.dia_semana,
                hora_inicio=f.hora_inicio,
                hora_fin=f.hora_fin,
                vigente_desde=f.vigente_desde,
                vigente_hasta=f.vigente_hasta,
            )
        )
    sesion.commit()
    return profesional


def un_sillon(sesion: Session, consultorio: ConsultorioModelo, **kw) -> SillonModelo:
    datos = {"nombre": "Sillón de Prueba", "activo": True}
    return _guardar(sesion, SillonModelo(consultorio_id=consultorio.id, **{**datos, **kw}))


def una_prestacion(sesion: Session, consultorio: ConsultorioModelo, **kw) -> PrestacionModelo:
    datos = {
        "nombre": f"Prestación de Prueba {next(_secuencia)}",
        "duracion_minutos": 30,
        "color": "#9E9E9E",
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
    creado_por: int | None = None,
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
            creado_por=creado_por,
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


CONTRASENA_DE_PRUEBA = "contrasena-ficticia-1"


def un_usuario(
    sesion: Session,
    consultorio: ConsultorioModelo,
    contrasena: str = CONTRASENA_DE_PRUEBA,
    activo: bool = True,
    token_version: int = 0,
    roles: tuple[Rol, ...] = (),
    **kw,
) -> UsuarioModelo:
    """Usuario ficticio con los ``roles`` indicados; el hash es bcrypt con 4 rondas (design J17)."""
    datos = {
        "email": f"usuario{next(_secuencia)}@consultorio-demo.test",
        "hash_password": HasherBcrypt(4).hashear(contrasena),
        "activo": activo,
        "token_version": token_version,
        "creado_en": RELOJ_FIJO,
    }
    usuario = _guardar(sesion, UsuarioModelo(consultorio_id=consultorio.id, **{**datos, **kw}))
    for rol in roles:
        sesion.add(UsuarioRolModelo(usuario_id=usuario.id, rol=rol.value))
    sesion.commit()
    return usuario


def un_bloqueo(
    sesion: Session,
    consultorio: ConsultorioModelo,
    *,
    inicio: datetime,
    fin: datetime,
    profesional: ProfesionalModelo | None = None,
    sillon: SillonModelo | None = None,
    motivo: str = "Ausencia",
    creado_por: int | None = None,
) -> BloqueoModelo:
    """Bloqueo guardado directo: del profesional, del sillón o, sin ninguno, de todo el consultorio.

    ``creado_por`` es NN (D282): si no se da, crea un usuario ficticio del consultorio.
    """
    if creado_por is None:
        creado_por = un_usuario(sesion, consultorio).id
    return _guardar(
        sesion,
        BloqueoModelo(
            consultorio_id=consultorio.id,
            profesional_id=None if profesional is None else profesional.id,
            sillon_id=None if sillon is None else sillon.id,
            inicio=inicio,
            fin=fin,
            motivo=motivo,
            creado_por=creado_por,
        ),
    )
