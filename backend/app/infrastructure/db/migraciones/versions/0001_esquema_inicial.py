"""Esquema inicial: las seis tablas de C-01 (INF-1).

Revisada a mano contra modelos.py. Las fechas son timestamptz: el tipo
FechaHoraUTC de la aplicación no se importa, una migración es una foto.

Revisión: 0001
Anterior: ninguna
Creada: 2026-10-13 12:32:09.498220
"""
from alembic import op
import sqlalchemy as sa


revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('consultorio',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(), nullable=False),
    sa.Column('slug', sa.String(), nullable=False),
    sa.Column('zona_horaria', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_consultorio')),
    sa.UniqueConstraint('slug', name=op.f('uq_consultorio_slug'))
    )
    op.create_table('paciente',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('consultorio_id', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(), nullable=False),
    sa.Column('apellido', sa.String(), nullable=False),
    sa.Column('telefono_whatsapp', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['consultorio_id'], ['consultorio.id'], name=op.f('fk_paciente_consultorio_id'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_paciente'))
    )
    op.create_index('ix_paciente_consultorio_telefono', 'paciente', ['consultorio_id', 'telefono_whatsapp'], unique=False)
    op.create_table('prestacion',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('consultorio_id', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(), nullable=False),
    sa.Column('duracion_minutos', sa.Integer(), nullable=False),
    sa.Column('activa', sa.Boolean(), nullable=False),
    sa.CheckConstraint('duracion_minutos > 0', name='ck_prestacion_duracion_positiva'),
    sa.ForeignKeyConstraint(['consultorio_id'], ['consultorio.id'], name=op.f('fk_prestacion_consultorio_id'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_prestacion')),
    sa.UniqueConstraint('consultorio_id', 'nombre', name=op.f('uq_prestacion_consultorio_id_nombre'))
    )
    op.create_table('profesional',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('consultorio_id', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['consultorio_id'], ['consultorio.id'], name=op.f('fk_profesional_consultorio_id'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_profesional'))
    )
    op.create_table('sillon',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('consultorio_id', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['consultorio_id'], ['consultorio.id'], name=op.f('fk_sillon_consultorio_id'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sillon'))
    )
    op.create_table('turno',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('consultorio_id', sa.Integer(), nullable=False),
    sa.Column('paciente_id', sa.Integer(), nullable=False),
    sa.Column('profesional_id', sa.Integer(), nullable=False),
    sa.Column('sillon_id', sa.Integer(), nullable=False),
    sa.Column('prestacion_id', sa.Integer(), nullable=False),
    sa.Column('inicio', sa.DateTime(timezone=True), nullable=False),
    sa.Column('fin', sa.DateTime(timezone=True), nullable=False),
    sa.Column('duracion_minutos', sa.Integer(), nullable=False),
    sa.Column('estado', sa.String(), nullable=False),
    sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('duracion_minutos > 0', name='ck_turno_duracion_positiva'),
    sa.CheckConstraint('inicio < fin', name='ck_turno_inicio_antes_de_fin'),
    sa.ForeignKeyConstraint(['consultorio_id'], ['consultorio.id'], name=op.f('fk_turno_consultorio_id'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['paciente_id'], ['paciente.id'], name=op.f('fk_turno_paciente_id'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['prestacion_id'], ['prestacion.id'], name=op.f('fk_turno_prestacion_id'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['profesional_id'], ['profesional.id'], name=op.f('fk_turno_profesional_id'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['sillon_id'], ['sillon.id'], name=op.f('fk_turno_sillon_id'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_turno'))
    )
    op.create_index('ix_turno_profesional_inicio_fin', 'turno', ['profesional_id', 'inicio', 'fin'], unique=False)
    op.create_index('ix_turno_sillon_inicio_fin', 'turno', ['sillon_id', 'inicio', 'fin'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_turno_sillon_inicio_fin', table_name='turno')
    op.drop_index('ix_turno_profesional_inicio_fin', table_name='turno')
    op.drop_table('turno')
    op.drop_table('sillon')
    op.drop_table('profesional')
    op.drop_table('prestacion')
    op.drop_index('ix_paciente_consultorio_telefono', table_name='paciente')
    op.drop_table('paciente')
    op.drop_table('consultorio')
