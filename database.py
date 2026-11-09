"""Persistência SQLite no schema final (v3): nomes separados."""
import os
import sqlite3
from datetime import datetime

CAMINHO_BANCO = os.environ.get("DB_PATH", "sistema.db")
SQL_CRIAR_TABELA = """
CREATE TABLE IF NOT EXISTS transacoes (
    id_transacao TEXT PRIMARY KEY,
    primeiro_nome TEXT NOT NULL,
    sobrenome TEXT NOT NULL,
    cpf TEXT NOT NULL,
    idade INTEGER,
    valor_bruto REAL,
    valor_final REAL,
    status TEXT CHECK (status IN ('APROVADO', 'REJEITADO')),
    motivo_rejeicao TEXT,
    data_processamento TIMESTAMP
)
"""
COLUNAS = (
    "id_transacao", "primeiro_nome", "sobrenome", "cpf", "idade",
    "valor_bruto", "valor_final", "status", "motivo_rejeicao",
    "data_processamento",
)

def conectar(caminho: str | None = None) -> sqlite3.Connection:
    conexao = sqlite3.connect(caminho or CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    return conexao

def inicializar_banco(conexao: sqlite3.Connection | None = None) -> None:
    """Cria o schema final para testes/execução isolada; produção usa Alembic."""
    conn = conexao or conectar()
    try:
        conn.execute(SQL_CRIAR_TABELA)
        conn.commit()
    finally:
        if conexao is None:
            conn.close()

def separar_nome(cliente: str) -> tuple[str, str]:
    partes = (cliente or "").strip().split()
    primeiro = partes[0] if partes else ""
    sobrenome = " ".join(partes[1:]) if len(partes) > 1 else ""
    return primeiro, sobrenome

def salvar_transacao(dados: dict, conexao: sqlite3.Connection | None = None) -> None:
    """Dual write durante a transição: aceita cliente e grava os campos novos."""
    primeiro = dados.get("primeiro_nome")
    sobrenome = dados.get("sobrenome")
    if primeiro is None or sobrenome is None:
        nome_legado = dados.get("cliente", "")
        nome_separado = separar_nome(nome_legado)
        primeiro = primeiro if primeiro is not None else nome_separado[0]
        sobrenome = sobrenome if sobrenome is not None else nome_separado[1]
    registro = {coluna: dados.get(coluna) for coluna in COLUNAS}
    registro["primeiro_nome"] = primeiro
    registro["sobrenome"] = sobrenome
    if registro["data_processamento"] is None:
        registro["data_processamento"] = datetime.now().isoformat(timespec="seconds")
    conn = conexao or conectar()
    try:
        # Durante a fase Expand, a coluna cliente ainda existe: grava nela
        # e nos novos campos (dual write). Após Contract, grava só os novos.
        nomes_colunas = {linha[1] for linha in conn.execute("PRAGMA table_info(transacoes)")}
        if "cliente" in nomes_colunas:
            registro["cliente"] = dados.get(
                "cliente", " ".join(p for p in (primeiro, sobrenome) if p)
            )
            colunas_atuais = COLUNAS + ("cliente",)
        else:
            colunas_atuais = COLUNAS
        colunas = ", ".join(colunas_atuais)
        marcadores = ", ".join(f":{c}" for c in colunas_atuais)
        sql = f"INSERT OR REPLACE INTO transacoes ({colunas}) VALUES ({marcadores})"
        conn.execute(sql, registro)
        conn.commit()
    finally:
        if conexao is None:
            conn.close()

def buscar_transacao_por_id(id_transacao: str, conexao: sqlite3.Connection | None = None) -> dict | None:
    conn = conexao or conectar()
    try:
        linha = conn.execute(
            "SELECT * FROM transacoes WHERE id_transacao = ?", (id_transacao,)
        ).fetchone()
        return dict(linha) if linha else None
    finally:
        if conexao is None:
            conn.close()
