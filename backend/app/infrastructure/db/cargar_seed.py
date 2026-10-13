"""Carga el seed ficticio en la base de ``DATABASE_URL`` (design I13).

Uso: ``python -m app.infrastructure.db.cargar_seed``. Espera una base ya migrada y se puede
repetir: si el seed ya está, no hace nada.
"""
from sqlalchemy.orm import Session

from app.infrastructure.configuracion import leer_database_url
from app.infrastructure.db.motor import crear_engine
from app.infrastructure.db.seed_demo import ajustar_secuencias, cargar_demo_si_falta


def main() -> None:
    engine = crear_engine(leer_database_url())
    try:
        with Session(engine) as sesion:
            cargado = cargar_demo_si_falta(sesion)
            if cargado:
                ajustar_secuencias(sesion)
    finally:
        engine.dispose()
    print("Seed cargado." if cargado else "El seed ya estaba cargado: no hizo falta.")


if __name__ == "__main__":
    main()
