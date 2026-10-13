"""Restricciones de exclusión: un profesional y un sillón no pueden tener dos turnos activos
solapados (INF-2, INF-3; DD-04, RN-AG-05, RN-AG-08, RN-AG-09, RN-AG-10).

La lista de estados activos va escrita como literal: una migración es una foto y no cambia
si mañana cambia el dominio. Los tests de INF-2 e INF-3 avisan si se desalinean.

Revisión: 0002
Anterior: 0001
"""
from alembic import op


revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        """
        ALTER TABLE turno ADD CONSTRAINT ex_turno_profesional_sin_solapamiento
            EXCLUDE USING gist (
                profesional_id WITH =,
                tstzrange(inicio, fin, '[)') WITH &&
            )
            WHERE (estado IN ('pendiente_aprobacion', 'pendiente_sena', 'reservado', 'confirmado'))
        """
    )
    op.execute(
        """
        ALTER TABLE turno ADD CONSTRAINT ex_turno_sillon_sin_solapamiento
            EXCLUDE USING gist (
                sillon_id WITH =,
                tstzrange(inicio, fin, '[)') WITH &&
            )
            WHERE (estado IN ('pendiente_aprobacion', 'pendiente_sena', 'reservado', 'confirmado'))
        """
    )


def downgrade() -> None:
    # No se quita la extensión btree_gist: puede haberla creado otro.
    op.execute("ALTER TABLE turno DROP CONSTRAINT ex_turno_sillon_sin_solapamiento")
    op.execute("ALTER TABLE turno DROP CONSTRAINT ex_turno_profesional_sin_solapamiento")
