"""cria tabelas iniciais

Revision ID: 0f19118b877f
Revises: 
Create Date: 2026-11-22 22:18:02.258735

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '0f19118b877f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('recurso',
    sa.Column('nome', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('patrimonio', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('categoria', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('disponivel', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recurso_nome'), 'recurso', ['nome'], unique=False)
    op.create_index(op.f('ix_recurso_patrimonio'), 'recurso', ['patrimonio'], unique=True)
    op.create_table('unidade',
    sa.Column('nome', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('endereco', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('predio', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('ativa', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_unidade_nome'), 'unidade', ['nome'], unique=False)
    op.create_table('usuario',
    sa.Column('nome', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('matricula', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('departamento', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usuario_email'), 'usuario', ['email'], unique=True)
    op.create_index(op.f('ix_usuario_matricula'), 'usuario', ['matricula'], unique=True)
    op.create_index(op.f('ix_usuario_nome'), 'usuario', ['nome'], unique=False)
    op.create_table('espaco',
    sa.Column('nome', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('tipo', sa.Enum('sala_reuniao', 'auditorio', 'laboratorio', 'sala_treinamento', 'multiuso', name='tipoespaco'), nullable=False),
    sa.Column('capacidade', sa.Integer(), nullable=False),
    sa.Column('descricao', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    sa.Column('unidade_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['unidade_id'], ['unidade.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_espaco_nome'), 'espaco', ['nome'], unique=False)
    op.create_table('bloqueioespaco',
    sa.Column('motivo', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('data_inicio', sa.DateTime(), nullable=False),
    sa.Column('data_fim', sa.DateTime(), nullable=False),
    sa.Column('espaco_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['espaco_id'], ['espaco.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('infraestruturaespaco',
    sa.Column('possui_projetor', sa.Boolean(), nullable=False),
    sa.Column('possui_som', sa.Boolean(), nullable=False),
    sa.Column('qtd_computadores', sa.Integer(), nullable=False),
    sa.Column('acessibilidade', sa.Boolean(), nullable=False),
    sa.Column('climatizado', sa.Boolean(), nullable=False),
    sa.Column('observacoes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('espaco_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['espaco_id'], ['espaco.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('espaco_id')
    )
    op.create_table('reserva',
    sa.Column('finalidade', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('qtd_participantes', sa.Integer(), nullable=False),
    sa.Column('data_inicio', sa.DateTime(), nullable=False),
    sa.Column('data_fim', sa.DateTime(), nullable=False),
    sa.Column('status', sa.Enum('confirmada', 'em_andamento', 'cancelada', 'concluida', name='statusreserva'), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('espaco_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['espaco_id'], ['espaco.id'], ),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('reservarecurso',
    sa.Column('reserva_id', sa.Integer(), nullable=False),
    sa.Column('recurso_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['recurso_id'], ['recurso.id'], ),
    sa.ForeignKeyConstraint(['reserva_id'], ['reserva.id'], ),
    sa.PrimaryKeyConstraint('reserva_id', 'recurso_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('reservarecurso')
    op.drop_table('reserva')
    op.drop_table('infraestruturaespaco')
    op.drop_table('bloqueioespaco')
    op.drop_index(op.f('ix_espaco_nome'), table_name='espaco')
    op.drop_table('espaco')
    op.drop_index(op.f('ix_usuario_nome'), table_name='usuario')
    op.drop_index(op.f('ix_usuario_matricula'), table_name='usuario')
    op.drop_index(op.f('ix_usuario_email'), table_name='usuario')
    op.drop_table('usuario')
    op.drop_index(op.f('ix_unidade_nome'), table_name='unidade')
    op.drop_table('unidade')
    op.drop_index(op.f('ix_recurso_patrimonio'), table_name='recurso')
    op.drop_index(op.f('ix_recurso_nome'), table_name='recurso')
    op.drop_table('recurso')
    # ### end Alembic commands ###
