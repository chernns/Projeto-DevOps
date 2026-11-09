"""Testes de integração de database.py usando SQLite em memória."""
import sqlite3
import pytest
import database

@pytest.fixture
def conexao():
    conn = database.conectar(":memory:")
    database.inicializar_banco(conn)
    yield conn
    conn.close()

def registro(**alteracoes):
    base = {
        "id_transacao": "TX1001",
        "cliente": "Carlos Eduardo Silva",
        "cpf": "12345678901",
        "idade": 25,
        "valor_bruto": 150.0,
        "valor_final": 150.0,
        "status": "APROVADO",
        "motivo_rejeicao": None,
    }
    base.update(alteracoes)
    return base

def test_inicializar_cria_tabela(conexao):
    tabela = conexao.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='transacoes'"
    ).fetchone()
    assert tabela is not None

def test_inicializar_e_idempotente(conexao):
    database.inicializar_banco(conexao)
    database.inicializar_banco(conexao)

def test_salvar_e_buscar_aprovado(conexao):
    database.salvar_transacao(registro(), conexao)
    salvo = database.buscar_transacao_por_id("TX1001", conexao)
    assert salvo["primeiro_nome"] == "Carlos"
    assert salvo["sobrenome"] == "Eduardo Silva"
    assert salvo["valor_final"] == 150.0
    assert salvo["status"] == "APROVADO"
    assert salvo["motivo_rejeicao"] is None
    assert salvo["data_processamento"] is not None
    assert "cliente" not in salvo

def test_salvar_e_buscar_rejeitado(conexao):
    database.salvar_transacao(registro(
        id_transacao="TX1005", valor_bruto=-50.0, valor_final=None,
        status="REJEITADO", motivo_rejeicao="Valor bruto deve ser maior que zero",
    ), conexao)
    salvo = database.buscar_transacao_por_id("TX1005", conexao)
    assert salvo["status"] == "REJEITADO"
    assert salvo["valor_final"] is None
    assert "maior que zero" in salvo["motivo_rejeicao"]

def test_buscar_inexistente_retorna_none(conexao):
    assert database.buscar_transacao_por_id("NAO_EXISTE", conexao) is None

def test_reprocessar_mesmo_id_atualiza_registro(conexao):
    database.salvar_transacao(registro(status="REJEITADO"), conexao)
    database.salvar_transacao(registro(status="APROVADO"), conexao)
    total = conexao.execute("SELECT COUNT(*) FROM transacoes").fetchone()[0]
    assert total == 1
    assert database.buscar_transacao_por_id("TX1001", conexao)["status"] == "APROVADO"

def test_status_invalido_e_bloqueado(conexao):
    with pytest.raises(sqlite3.IntegrityError):
        database.salvar_transacao(registro(status="PENDENTE"), conexao)

def test_funcoes_sem_conexao_usam_arquivo(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "CAMINHO_BANCO", str(tmp_path / "teste.db"))
    database.inicializar_banco()
    database.salvar_transacao(registro())
    salvo = database.buscar_transacao_por_id("TX1001")
    assert salvo["cpf"] == "12345678901"
    assert salvo["primeiro_nome"] == "Carlos"

def test_separar_nome_com_nome_simples():
    assert database.separar_nome("Ana") == ("Ana", "")

def test_grava_campos_novos_informados_diretamente(conexao):
    dados = registro(primeiro_nome="Carlos", sobrenome="Silva")
    database.salvar_transacao(dados, conexao)
    salvo = database.buscar_transacao_por_id("TX1001", conexao)
    assert (salvo["primeiro_nome"], salvo["sobrenome"]) == ("Carlos", "Silva")


def test_dual_write_enquanto_coluna_legada_existe():
    conn = database.conectar(":memory:")
    conn.execute("""CREATE TABLE transacoes (
        id_transacao TEXT PRIMARY KEY, cliente TEXT, primeiro_nome TEXT,
        sobrenome TEXT, cpf TEXT NOT NULL, idade INTEGER, valor_bruto REAL,
        valor_final REAL, status TEXT, motivo_rejeicao TEXT,
        data_processamento TIMESTAMP
    )""")
    database.salvar_transacao(registro(), conn)
    salvo = conn.execute(
        "SELECT cliente, primeiro_nome, sobrenome FROM transacoes WHERE id_transacao='TX1001'"
    ).fetchone()
    assert tuple(salvo) == ("Carlos Eduardo Silva", "Carlos", "Eduardo Silva")
    conn.close()
