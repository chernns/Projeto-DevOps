"""Remove o campo legado cliente após backfill e dual write.

Revision ID: 0004_contract
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_contract"
down_revision = "0003_backfill"
branch_labels = None
depends_on = None

def upgrade():
    # A migração só remove cliente quando todos os registros têm os novos campos.
    conn = op.get_bind()
    pendentes = conn.exec_driver_sql(
        "SELECT COUNT(*) FROM transacoes "
        "WHERE primeiro_nome IS NULL OR sobrenome IS NULL"
    ).scalar_one()
    if pendentes:
        raise RuntimeError(
            f"Contract cancelado: existem {pendentes} registros sem nome/sobrenome preenchidos."
        )
    with op.batch_alter_table("transacoes") as batch_op:
        batch_op.drop_column("cliente")

def downgrade():
    with op.batch_alter_table("transacoes") as batch_op:
        batch_op.add_column(sa.Column("cliente", sa.Text(), nullable=True))
    conn = op.get_bind()
    rows = conn.exec_driver_sql(
        "SELECT id_transacao, primeiro_nome, sobrenome FROM transacoes"
    ).fetchall()
    for identificador, primeiro, sobrenome in rows:
        nome = " ".join(p for p in (primeiro, sobrenome) if p)
        conn.exec_driver_sql(
            "UPDATE transacoes SET cliente = ? WHERE id_transacao = ?",
            (nome, identificador),
        )
