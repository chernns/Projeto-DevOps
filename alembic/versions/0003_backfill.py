"""Preenche os novos campos a partir do campo legado cliente.

Revision ID: 0003_backfill
"""
from alembic import op

revision = "0003_backfill"
down_revision = "0002_expand"
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    registros = conn.exec_driver_sql(
        "SELECT id_transacao, cliente FROM transacoes"
    ).fetchall()
    for identificador, cliente in registros:
        partes = (cliente or "").strip().split()
        primeiro = partes[0] if partes else ""
        sobrenome = " ".join(partes[1:]) if len(partes) > 1 else ""
        conn.exec_driver_sql(
            "UPDATE transacoes SET primeiro_nome = ?, sobrenome = ? WHERE id_transacao = ?",
            (primeiro, sobrenome, identificador),
        )

def downgrade():
    # O campo cliente ainda existe; não há dados a remover.
    pass
