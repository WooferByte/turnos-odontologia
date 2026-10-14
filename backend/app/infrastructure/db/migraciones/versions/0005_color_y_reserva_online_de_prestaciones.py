"""Color y reserva en línea de las prestaciones (US-001 CA-1; DD-15, D130, D174).

Generada con autogenerate y revisada a mano contra modelos.py. Las dos columnas son NOT NULL:
se agregan con un server_default que completa las filas que ya existen (gris #9E9E9E y no
reservable) y después se lo quita, para que la base quede igual que el modelo, que no lleva
default de base. Nada destructivo: el downgrade solo quita las dos columnas.

Revisión: 0005
Anterior: 0004
"""
from alembic import op
import sqlalchemy as sa


revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('prestacion', sa.Column('color', sa.String(), server_default='#9E9E9E', nullable=False))
    op.add_column('prestacion', sa.Column('reservable_online', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.alter_column('prestacion', 'color', server_default=None)
    op.alter_column('prestacion', 'reservable_online', server_default=None)


def downgrade() -> None:
    op.drop_column('prestacion', 'reservable_online')
    op.drop_column('prestacion', 'color')
