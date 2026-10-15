"""Roles y creador: usuario_rol y las columnas profesional.usuario_id, profesional.matricula y turno.creado_por.

(US-091, US-092; RN-AU-02, RN-AU-05; DD-15, D213, D215.)

Generada con autogenerate y revisada a mano contra modelos.py. Las tres columnas son nulas: no
reescriben la tabla turno ni exigen datos previos. El UNIQUE de profesional.usuario_id es simple
(admite varios nulos). El CHECK del rol acota la lista cerrada de RN-AU-05 (D213). Sin datos: los
roles y el vínculo del seed los pone cargar_seed, no la migración. El downgrade quita solo lo que
esta migración creó; los roles guardados y el creador de los turnos se pierden con él.

Revisión: 0007
Anterior: 0006
"""
from alembic import op
import sqlalchemy as sa


revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('usuario_rol',
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('rol', sa.String(), nullable=False),
    sa.CheckConstraint("rol IN ('odontologo', 'recepcionista', 'dueno')", name='ck_usuario_rol_rol_valido'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], name=op.f('fk_usuario_rol_usuario_id'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('usuario_id', 'rol', name=op.f('pk_usuario_rol'))
    )
    op.add_column('profesional', sa.Column('usuario_id', sa.Integer(), nullable=True))
    op.add_column('profesional', sa.Column('matricula', sa.String(), nullable=True))
    op.create_unique_constraint(op.f('uq_profesional_usuario_id'), 'profesional', ['usuario_id'])
    op.create_foreign_key(op.f('fk_profesional_usuario_id'), 'profesional', 'usuario', ['usuario_id'], ['id'], ondelete='RESTRICT')
    op.add_column('turno', sa.Column('creado_por', sa.Integer(), nullable=True))
    op.create_foreign_key(op.f('fk_turno_creado_por'), 'turno', 'usuario', ['creado_por'], ['id'], ondelete='RESTRICT')


def downgrade() -> None:
    op.drop_constraint(op.f('fk_turno_creado_por'), 'turno', type_='foreignkey')
    op.drop_column('turno', 'creado_por')
    op.drop_constraint(op.f('fk_profesional_usuario_id'), 'profesional', type_='foreignkey')
    op.drop_constraint(op.f('uq_profesional_usuario_id'), 'profesional', type_='unique')
    op.drop_column('profesional', 'matricula')
    op.drop_column('profesional', 'usuario_id')
    op.drop_table('usuario_rol')
