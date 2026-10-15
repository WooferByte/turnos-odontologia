"""Carga el seed ficticio en la base de ``DATABASE_URL`` (design I13).

Uso: ``python -m app.infrastructure.db.cargar_seed``. Espera una base ya migrada y se puede
repetir: si el seed ya está, no hace nada.
"""
import os
from collections.abc import Mapping

from sqlalchemy.orm import Session

from app.infrastructure.configuracion import leer_contrasena_del_seed, leer_database_url
from app.infrastructure.db.motor import crear_engine
from app.infrastructure.db.seed_demo import (
    ajustar_secuencias,
    cargar_demo_si_falta,
    cargar_recepcionista_demo_si_falta,
    cargar_roles_demo_si_faltan,
    cargar_usuario_demo_si_falta,
)
from app.infrastructure.seguridad.contrasenas import HasherBcrypt


def main(entorno: Mapping[str, str] = os.environ) -> None:
    url = leer_database_url(entorno)
    contrasena = leer_contrasena_del_seed(entorno)  # falla antes de abrir la base
    hash_password = HasherBcrypt().hashear(contrasena)
    engine = crear_engine(url)
    try:
        with Session(engine) as sesion:
            consultorio_cargado = cargar_demo_si_falta(sesion)
            usuario_cargado = cargar_usuario_demo_si_falta(sesion, hash_password)
            roles_cargados = cargar_roles_demo_si_faltan(sesion)
            recepcionista_cargada = cargar_recepcionista_demo_si_falta(sesion, hash_password)
            cargado = (
                consultorio_cargado or usuario_cargado or roles_cargados or recepcionista_cargada
            )
            if cargado:
                ajustar_secuencias(sesion)
    finally:
        engine.dispose()
    print("Seed cargado." if cargado else "El seed ya estaba cargado: no hizo falta.")


if __name__ == "__main__":
    main()
