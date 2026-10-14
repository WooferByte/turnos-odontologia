"""Piezas compartidas de la documentación OpenAPI de los routers (design P14)."""
from app.api.esquemas import Problema

# Los errores salen como application/problem+json (RFC 7807). "model" registra el esquema
# Problema; FastAPI lo publica además bajo application/json, que acá no se usa.
_PROBLEMA_JSON = {
    "application/problem+json": {"schema": {"$ref": "#/components/schemas/Problema"}}
}


def _respuesta_de_error(descripcion: str) -> dict:
    return {"description": descripcion, "model": Problema, "content": _PROBLEMA_JSON}
