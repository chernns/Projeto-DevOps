"""Adiciona primeiro_nome e sobrenome sem remover cliente.

Revision ID: 0002_expand
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_expand"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table("transacoes") as batch_op:
        batch_op.add_column(sa.Column("primeiro_nome", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("sobrenome", sa.Text(), nullable=True))
        batch_op.alter_column("cliente", existing_type=sa.Text(), nullable=True)

def downgrade():
    with op.batch_alter_table("transacoes") as batch_op:
        batch_op.alter_column("cliente", existing_type=sa.Text(), nullable=False)
        batch_op.drop_column("sobrenome")
        batch_op.drop_column("primeiro_nome")
