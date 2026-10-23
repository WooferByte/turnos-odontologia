"""Horario recurrente: la tabla franja_horaria (US-002 CA-1; RN-AG-04, RN-AG-16; DD-15, D257, D259).

Generada con autogenerate y revisada a mano contra modelos.py. Solo crea la tabla nueva: no toca
las existentes ni carga datos (el horario de la demo lo pone el seed). Los CHECK de la base son la
red de seguridad del dominio: el día va de 0 a 6, la hora de inicio es anterior a la de fin y la
vigencia, si tiene las dos fechas, no está invertida. No hay restricción de exclusión para franjas
superpuestas: el PUT valida antes y reemplaza todo en una transacción. El downgrade borra la
tabla y con ella las franjas guardadas.

Revisión: 0008
Anterior: 0007
"""
from alembic import op
import sqlalchemy as sa


revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('franja_horaria',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('profesional_id', sa.Integer(), nullable=False),
    sa.Column('dia_semana', sa.SmallInteger(), nullable=False),
    sa.Column('hora_inicio', sa.Time(), nullable=False),
    sa.Column('hora_fin', sa.Time(), nullable=False),
    sa.Column('vigente_desde', sa.Date(), nullable=True),
    sa.Column('vigente_hasta', sa.Date(), nullable=True),
    sa.CheckConstraint('dia_semana BETWEEN 0 AND 6', name='ck_franja_horaria_dia_semana'),
    sa.CheckConstraint('hora_inicio < hora_fin', name='ck_franja_horaria_inicio_antes_del_fin'),
    sa.CheckConstraint('vigente_desde IS NULL OR vigente_hasta IS NULL OR vigente_hasta >= vigente_desde', name='ck_franja_horaria_vigencia'),
    sa.ForeignKeyConstraint(['profesional_id'], ['profesional.id'], name=op.f('fk_franja_horaria_profesional_id'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_franja_horaria'))
    )
    op.create_index('ix_franja_horaria_profesional_dia', 'franja_horaria', ['profesional_id', 'dia_semana'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_franja_horaria_profesional_dia', table_name='franja_horaria')
    op.drop_table('franja_horaria')
