"""Traducción de los errores de dominio a HTTP (D4). Solo esta capa conoce estados, ``type`` y ``title``."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.esquemas import ConflictoSalida, ErrorDeCampoSalida, Problema, ReferenciaSalida
from app.domain.errors import (
    EntradaInvalida,
    ErrorDeDominio,
    ErrorDeSolapamiento,
    FechaNoUTC,
    IntervaloInvalido,
)

MEDIA_TYPE_PROBLEMA = "application/problem+json"
MENSAJE_FECHA_NO_UTC = (
    "La fecha y hora debe tener zona y estar en UTC, por ejemplo 2026-11-02T13:00:00Z."
)

# clase del error -> (estado, type, title). Una clase que no esté acá es un error de programación.
_CLASES_DE_ERROR: dict[type[ErrorDeDominio], tuple[int, str, str]] = {
    ErrorDeSolapamiento: (409, "/errores/solapamiento-turno", "Turno solapado"),
    IntervaloInvalido: (422, "/errores/intervalo-invalido", "Intervalo inválido"),
    EntradaInvalida: (422, "/errores/entrada-invalida", "Entrada inválida"),
}


def _problemas(cantidad: int) -> str:
    return f"{cantidad} problema" if cantidad == 1 else f"{cantidad} problemas"


def _detalle_de_solapamiento(error: ErrorDeSolapamiento) -> str:
    recursos = {c.recurso for c in error.conflictos}
    if recursos == {"profesional", "sillon"}:
        return "El profesional y el sillón ya tienen un turno activo en ese horario."
    return f"El {recursos.pop()} ya tiene un turno activo en ese horario."


def _problema_de_entrada(problema: dict, error: EntradaInvalida) -> Problema:
    errores = [
        ErrorDeCampoSalida(campo=e.campo, codigo=e.codigo, mensaje=MENSAJE_FECHA_NO_UTC)
        for e in error.errores
        if isinstance(e, FechaNoUTC)
    ]
    referencias = [
        ReferenciaSalida(recurso=r.recurso, recurso_id=r.recurso_id, motivo=r.motivo)
        for r in error.referencias
    ]
    partes = [f"{e.campo} debe tener zona y estar en UTC" for e in errores] + [
        f"{r.recurso} {r.recurso_id} ({r.motivo})" for r in referencias
    ]
    problema["detail"] = (
        f"La petición tiene {_problemas(len(partes))} de entrada: " + "; ".join(partes) + "."
    )
    return Problema(**problema, referencias=referencias, errores=errores)


def _problema_de(error: ErrorDeDominio, estado: int, tipo: str, titulo: str, ruta: str) -> Problema:
    base = {
        "type": tipo,
        "title": titulo,
        "status": estado,
        "instance": ruta,
        "codigos": error.codigos,
    }
    if isinstance(error, ErrorDeSolapamiento):
        conflictos = [
            ConflictoSalida(
                codigo=c.codigo, recurso=c.recurso, recurso_id=c.recurso_id, turno_id=c.turno_id
            )
            for c in error.conflictos
        ]
        return Problema(**base, detail=_detalle_de_solapamiento(error), conflictos=conflictos)
    if isinstance(error, EntradaInvalida):
        return _problema_de_entrada(base, error)
    return Problema(**base, detail="El turno no puede cruzar la medianoche del consultorio.")


def _responder(problema: Problema) -> JSONResponse:
    return JSONResponse(
        status_code=problema.status,
        content=problema.model_dump(exclude_unset=True),
        media_type=MEDIA_TYPE_PROBLEMA,
    )


def _manejar_error_de_dominio(request: Request, error: ErrorDeDominio) -> JSONResponse:
    clase = _CLASES_DE_ERROR.get(type(error))
    if clase is None:
        raise error  # error de programación: se deja subir (500), no se inventa un estado
    estado, tipo, titulo = clase
    return _responder(_problema_de(error, estado, tipo, titulo, request.url.path))


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(ErrorDeDominio, _manejar_error_de_dominio)
