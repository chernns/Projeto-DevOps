"""Cria o schema original (v1), com o campo cliente.

Revision ID: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "transacoes",
        sa.Column("id_transacao", sa.Text(), primary_key=True),
        sa.Column("cliente", sa.Text(), nullable=False),
        sa.Column("cpf", sa.Text(), nullable=False),
        sa.Column("idade", sa.Integer()),
        sa.Column("valor_bruto", sa.Float()),
        sa.Column("valor_final", sa.Float()),
        sa.Column("status", sa.Text()),
        sa.Column("motivo_rejeicao", sa.Text()),
        sa.Column("data_processamento", sa.DateTime()),
        sa.CheckConstraint("status IN ('APROVADO', 'REJEITADO')", name="ck_transacoes_status"),
    )

def downgrade():
    op.drop_table("transacoes")
