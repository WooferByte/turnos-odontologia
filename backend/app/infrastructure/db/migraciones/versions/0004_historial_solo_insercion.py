"""Historial de solo inserción: PostgreSQL rechaza UPDATE, DELETE y TRUNCATE de evento_turno.

SQL literal que no está en el modelo (como la restricción de exclusión de 0002): una función
de disparador y dos disparadores. Frena también al dueño de la tabla, que es el usuario con el
que se conecta la aplicación; no frena un DROP TABLE (el downgrade de 0003 lo necesita) ni a un
superusuario que deshabilite el disparador (US-015 CA-1, RN-AG-11; design H11).

Revisión: 0004
Anterior: 0003
"""
from alembic import op


revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION evento_turno_solo_insercion() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'evento_turno es de solo inserción (RN-AG-11)';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER tg_evento_turno_sin_modificar
            BEFORE UPDATE OR DELETE ON evento_turno
            FOR EACH ROW EXECUTE FUNCTION evento_turno_solo_insercion()
        """
    )
    op.execute(
        """
        CREATE TRIGGER tg_evento_turno_sin_vaciar
            BEFORE TRUNCATE ON evento_turno
            FOR EACH STATEMENT EXECUTE FUNCTION evento_turno_solo_insercion()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER tg_evento_turno_sin_vaciar ON evento_turno")
    op.execute("DROP TRIGGER tg_evento_turno_sin_modificar ON evento_turno")
    op.execute("DROP FUNCTION evento_turno_solo_insercion()")
