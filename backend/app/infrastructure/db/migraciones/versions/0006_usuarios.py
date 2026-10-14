"""Usuarios del panel: la tabla usuario (US-090, US-094; RN-AU-03, RN-AU-04; DD-15, D199).

Generada con autogenerate y revisada a mano contra modelos.py. La fecha es timestamptz: el tipo
FechaHoraUTC de la aplicación no se importa, una migración es una foto. El email se guarda
normalizado (sin espacios y en minúsculas) y su UNIQUE es simple. Sin server_default: los valores
por defecto los pone la aplicación. El downgrade quita solo la tabla usuario y no toca las demás.

Revisión: 0006
Anterior: 0005
"""
from alembic import op
import sqlalchemy as sa


revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('usuario',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('consultorio_id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('hash_password', sa.String(), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('token_version', sa.Integer(), nullable=False),
    sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['consultorio_id'], ['consultorio.id'], name=op.f('fk_usuario_consultorio_id'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_usuario')),
    sa.UniqueConstraint('email', name=op.f('uq_usuario_email'))
    )


def downgrade() -> None:
    op.drop_table('usuario')
