"""Bloqueos puntuales: la tabla bloqueo (US-003 CA-1; RN-AG-04b, RN-AG-17; DD-15, D272, D282).

Generada con autogenerate y revisada a mano contra modelos.py. Solo crea la tabla nueva: no toca
las existentes ni carga datos (la demo arranca sin bloqueos, D284). Los CHECK de la base son la red
de seguridad del dominio: el bloqueo termina después de empezar y no lleva profesional y sillón a
la vez (D272). ``inicio`` y ``fin`` son fechas con zona. El downgrade borra la tabla y con ella los
bloqueos guardados.

Revisión: 0009
Anterior: 0008
"""
from alembic import op
import sqlalchemy as sa


revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('bloqueo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('consultorio_id', sa.Integer(), nullable=False),
    sa.Column('profesional_id', sa.Integer(), nullable=True),
    sa.Column('sillon_id', sa.Integer(), nullable=True),
    sa.Column('inicio', sa.DateTime(timezone=True), nullable=False),
    sa.Column('fin', sa.DateTime(timezone=True), nullable=False),
    sa.Column('motivo', sa.String(length=200), nullable=False),
    sa.Column('creado_por', sa.Integer(), nullable=False),
    sa.CheckConstraint('inicio < fin', name='ck_bloqueo_inicio_antes_de_fin'),
    sa.CheckConstraint('NOT (profesional_id IS NOT NULL AND sillon_id IS NOT NULL)', name='ck_bloqueo_un_solo_recurso'),
    sa.ForeignKeyConstraint(['consultorio_id'], ['consultorio.id'], name=op.f('fk_bloqueo_consultorio_id'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['creado_por'], ['usuario.id'], name=op.f('fk_bloqueo_creado_por'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['profesional_id'], ['profesional.id'], name=op.f('fk_bloqueo_profesional_id'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['sillon_id'], ['sillon.id'], name=op.f('fk_bloqueo_sillon_id'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bloqueo'))
    )
    op.create_index('ix_bloqueo_consultorio', 'bloqueo', ['consultorio_id', 'inicio'], unique=False)
    op.create_index('ix_bloqueo_profesional', 'bloqueo', ['profesional_id', 'inicio', 'fin'], unique=False)
    op.create_index('ix_bloqueo_sillon', 'bloqueo', ['sillon_id', 'inicio', 'fin'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_bloqueo_sillon', table_name='bloqueo')
    op.drop_index('ix_bloqueo_profesional', table_name='bloqueo')
    op.drop_index('ix_bloqueo_consultorio', table_name='bloqueo')
    op.drop_table('bloqueo')
