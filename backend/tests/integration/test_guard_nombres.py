"""Guard de nombres estables para las restricciones (design I4, INF-1)."""
from sqlalchemy import ForeignKeyConstraint, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.sql.schema import Constraint

from app.infrastructure.db.modelos import Base

PREFIJOS = {
    PrimaryKeyConstraint: "pk_",
    ForeignKeyConstraint: "fk_",
    UniqueConstraint: "uq_",
}


def _restricciones_con_nombre_obligatorio() -> list[tuple[str, Constraint, str]]:
    encontradas = []
    for tabla in Base.metadata.sorted_tables:
        for restriccion in tabla.constraints:
            for tipo, prefijo in PREFIJOS.items():
                if type(restriccion) is tipo:
                    encontradas.append((tabla.name, restriccion, prefijo))
    return encontradas


def test_toda_clave_y_restriccion_unica_tiene_nombre() -> None:
    sin_nombre_valido = [
        f"{tabla}: {type(restriccion).__name__} nombre={restriccion.name!r} (se esperaba prefijo {prefijo})"
        for tabla, restriccion, prefijo in _restricciones_con_nombre_obligatorio()
        if not str(restriccion.name or "").startswith(prefijo)
    ]
    assert not sin_nombre_valido, "Restricciones sin nombre estable:\n" + "\n".join(sin_nombre_valido)


def test_el_guard_ve_las_claves_las_foraneas_y_las_unicas_de_las_seis_tablas() -> None:
    tipos = {type(restriccion) for _, restriccion, _ in _restricciones_con_nombre_obligatorio()}
    assert tipos == set(PREFIJOS)
