"""Traducción de los errores de dominio a HTTP (D4). Solo esta capa conoce estados, ``type`` y ``title``."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.esquemas import ConflictoSalida, ErrorDeCampoSalida, Problema, ReferenciaSalida
from app.domain.errors import (
    BloqueoInvertido,
    AdministracionSinOdontologo,
    ContrasenaFueraDeRango,
    CredencialesInvalidas,
    DuracionInvalida,
    EmailRepetido,
    EntradaInvalida,
    ErrorDeDominio,
    ErrorDeSolapamiento,
    FechaNoUTC,
    FranjaInvalida,
    FueraDeHorario,
    IntervaloInvalido,
    NombreDePrestacionRepetido,
    PermisoInsuficiente,
    RecursoDeLaUrlNoEncontrado,
    SesionInvalida,
)

MEDIA_TYPE_PROBLEMA = "application/problem+json"
MENSAJE_FECHA_NO_UTC = (
    "La fecha y hora debe tener zona y estar en UTC, por ejemplo 2026-11-02T13:00:00Z."
)

# clase del error -> (estado, type, title). Una clase que no esté acá es un error de programación.
_CLASES_DE_ERROR: dict[type[ErrorDeDominio], tuple[int, str, str]] = {
    ErrorDeSolapamiento: (409, "/errores/solapamiento-turno", "Turno solapado"),
    IntervaloInvalido: (422, "/errores/intervalo-invalido", "Intervalo inválido"),
    FueraDeHorario: (422, "/errores/fuera-de-horario", "Fuera de horario"),
    EntradaInvalida: (422, "/errores/entrada-invalida", "Entrada inválida"),
    RecursoDeLaUrlNoEncontrado: (404, "/errores/recurso-no-encontrado", "Recurso no encontrado"),
    NombreDePrestacionRepetido: (409, "/errores/nombre-repetido", "Nombre repetido"),
    CredencialesInvalidas: (401, "/errores/credenciales-invalidas", "Credenciales inválidas"),
    SesionInvalida: (401, "/errores/sesion-invalida", "Sesión inválida"),
    PermisoInsuficiente: (403, "/errores/permiso-insuficiente", "Permiso insuficiente"),
    EmailRepetido: (409, "/errores/email-repetido", "Email repetido"),
    AdministracionSinOdontologo: (409, "/errores/administracion-sin-odontologo", "Operación no permitida"),
}
# Los dos 401 llevan RFC 6750 §3 y un texto fijo que no depende de la causa (design J13).
_CABECERAS_DE_NO_AUTENTICADO = {"WWW-Authenticate": "Bearer"}
_ERRORES_DE_TEXTO_FIJO = (
    NombreDePrestacionRepetido,
    CredencialesInvalidas,
    SesionInvalida,
    PermisoInsuficiente,
    EmailRepetido,
    AdministracionSinOdontologo,
    FueraDeHorario,
)


ErrorDeCampo = FechaNoUTC | DuracionInvalida | ContrasenaFueraDeRango | FranjaInvalida | BloqueoInvertido


def _problemas(cantidad: int) -> str:
    return f"{cantidad} problema" if cantidad == 1 else f"{cantidad} problemas"


def _detalle_de_solapamiento(error: ErrorDeSolapamiento) -> str:
    recursos = {c.recurso for c in error.conflictos}
    if recursos == {"profesional", "sillon"}:
        return "El profesional y el sillón ya tienen un turno activo en ese horario."
    if recursos == {"sillon"}:
        return "El sillón ya tiene un turno activo en ese horario."
    return "El profesional ya tiene un turno activo en ese horario."


def _texto_de_referencia(referencia: ReferenciaSalida) -> str:
    """prestacion 999 (inexistente); sin id si el recurso se omitió (sillon (varios_activos))."""
    recurso = referencia.recurso
    if referencia.recurso_id is not None:
        recurso = f"{recurso} {referencia.recurso_id}"
    return f"{recurso} ({referencia.motivo})"


def _error_de_campo(error: ErrorDeCampo) -> ErrorDeCampoSalida:
    """Cada error de campo lleva su propio mensaje (design P5)."""
    mensaje = MENSAJE_FECHA_NO_UTC if isinstance(error, FechaNoUTC) else error.mensaje
    return ErrorDeCampoSalida(campo=error.campo, codigo=error.codigo, mensaje=mensaje)


def _texto_de_error_de_campo(error: ErrorDeCampo) -> str:
    if isinstance(error, FechaNoUTC):
        return f"{error.campo} debe tener zona y estar en UTC"
    if isinstance(error, ContrasenaFueraDeRango):
        return f"{error.campo} debe tener de 10 caracteres a 72 bytes"
    if isinstance(error, (FranjaInvalida, BloqueoInvertido)):
        return error.mensaje
    return f"{error.campo} debe ser mayor que 0 y múltiplo de {error.granularidad} minutos"


def _problema_de_entrada(problema: dict, error: EntradaInvalida) -> Problema:
    de_campo = [e for e in error.errores if isinstance(e, (FechaNoUTC, DuracionInvalida, ContrasenaFueraDeRango, FranjaInvalida, BloqueoInvertido))]
    errores = [_error_de_campo(e) for e in de_campo]
    referencias = [
        ReferenciaSalida(recurso=r.recurso, recurso_id=r.recurso_id, motivo=r.motivo)
        for r in error.referencias
    ]
    partes = [_texto_de_error_de_campo(e) for e in de_campo] + [
        _texto_de_referencia(r) for r in referencias
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
    if isinstance(error, RecursoDeLaUrlNoEncontrado):
        referencias = [
            ReferenciaSalida(recurso=r.recurso, recurso_id=r.recurso_id, motivo=r.motivo)
            for r in error.referencias
        ]
        return Problema(**base, detail=error.mensaje, referencias=referencias)
    if isinstance(error, _ERRORES_DE_TEXTO_FIJO):
        return Problema(**base, detail=error.mensaje)
    return Problema(**base, detail="El turno no puede cruzar la medianoche del consultorio.")


def _responder(problema: Problema, cabeceras: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=problema.status,
        content=problema.model_dump(exclude_unset=True),
        media_type=MEDIA_TYPE_PROBLEMA,
        headers=cabeceras,
    )


def _manejar_error_de_dominio(request: Request, error: ErrorDeDominio) -> JSONResponse:
    # La primera clase de la cadena de herencia que esté en el mapa: las subclases resuelven como su base.
    clase = next((_CLASES_DE_ERROR[c] for c in type(error).__mro__ if c in _CLASES_DE_ERROR), None)
    if clase is None:
        raise error  # error de programación: se deja subir (500), no se inventa un estado
    estado, tipo, titulo = clase
    cabeceras = _CABECERAS_DE_NO_AUTENTICADO if estado == 401 else None
    return _responder(_problema_de(error, estado, tipo, titulo, request.url.path), cabeceras)


def _campo_de(ubicacion: tuple) -> str | None:
    """Ubicación de Pydantic sin el prefijo body ni path, unida con puntos; None si es del cuerpo."""
    partes = [str(parte) for parte in ubicacion if parte not in ("body", "path")]
    return ".".join(partes) or None


def _manejar_cuerpo_mal_formado(request: Request, error: RequestValidationError) -> JSONResponse:
    errores = [
        ErrorDeCampoSalida(
            # Un JSON roto no apunta a ningún campo: su ubicación es la posición del texto.
            campo=None if e["type"] == "json_invalid" else _campo_de(e["loc"]),
            codigo=None,
            mensaje=e["msg"],
        )
        for e in error.errors()
    ]
    estado, tipo, titulo = _CLASES_DE_ERROR[EntradaInvalida]
    origen = "el cuerpo" if any(e["loc"][0] == "body" for e in error.errors()) else "la ruta"
    return _responder(
        Problema(
            type=tipo,
            title=titulo,
            status=estado,
            detail=(
                f"La petición tiene {_problemas(len(errores))} de entrada: "
                f"{origen} no tiene el formato esperado."
            ),
            instance=request.url.path,
            codigos=[],
            referencias=[],
            errores=errores,
        )
    )


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(ErrorDeDominio, _manejar_error_de_dominio)
    app.add_exception_handler(RequestValidationError, _manejar_cuerpo_mal_formado)
