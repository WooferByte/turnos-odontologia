"""Paciente nuevo: la columna paciente.es_nuevo (US-014 CA-4; RN-TD-05; DD-15, D52, D99, D361).

Generada con autogenerate y revisada a mano contra modelos.py. Agrega la columna no nula con
``server_default`` (en PostgreSQL 17 eso no reescribe la tabla) y la rellena en la misma
migración: un paciente con algún turno ``atendido`` queda en ``false`` (la columna es cierta por
definición en cualquier base migrada, aunque hoy ningún camino de la API deje un turno atendido).
El ``server_default`` se conserva: un INSERT sin la columna, como el del seed, sigue valiendo.
El downgrade borra la columna (se pierde el dato; se recalcula al volver a aplicar el relleno).

Revisión: 0010
Anterior: 0009
"""
from alembic import op
import sqlalchemy as sa


revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('paciente', sa.Column('es_nuevo', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.execute(
        "UPDATE paciente SET es_nuevo = false WHERE EXISTS "
        "(SELECT 1 FROM turno WHERE turno.paciente_id = paciente.id AND turno.estado = 'atendido')"
    )


def downgrade() -> None:
    op.drop_column('paciente', 'es_nuevo')
