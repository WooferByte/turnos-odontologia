"""Historial de turnos: la tabla evento_turno y su índice (E9, US-015 CA-1; RN-AG-11).

Revisada a mano contra modelos.py. La fecha es timestamptz: el tipo FechaHoraUTC de la
aplicación no se importa, una migración es una foto. El disparador de solo inserción
va aparte, en 0004.

Revisión: 0003
Anterior: 0002
"""
from alembic import op
import sqlalchemy as sa


revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('evento_turno',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('turno_id', sa.Integer(), nullable=False),
    sa.Column('tipo', sa.String(), nullable=False),
    sa.Column('actor_tipo', sa.String(), nullable=False),
    sa.Column('actor_id', sa.String(), nullable=True),
    sa.Column('ocurrido_en', sa.DateTime(timezone=True), nullable=False),
    sa.Column('antes', sa.JSON(), nullable=True),
    sa.Column('despues', sa.JSON(), nullable=True),
    sa.Column('motivo', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['turno_id'], ['turno.id'], name=op.f('fk_evento_turno_turno_id'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_evento_turno'))
    )
    op.create_index('ix_evento_turno_turno_id_ocurrido_en', 'evento_turno', ['turno_id', 'ocurrido_en'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_evento_turno_turno_id_ocurrido_en', table_name='evento_turno')
    op.drop_table('evento_turno')
