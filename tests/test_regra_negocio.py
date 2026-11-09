"""Testes unitários de regra_negocio.py.

Técnicas aplicadas:
- Particionamento de Equivalência: classes válidas/inválidas de valor, idade, CPF e categoria.
- Análise de Valores-Limite: 0/0.01 (valor), -1/0/120/121 (idade), 17/18 (maioridade),
  59/60 (idoso), 10/11/12 dígitos (CPF).
"""

import json
from pathlib import Path

import pytest

from regra_negocio import calcular_desconto_e_final, validar_transacao


def transacao(**alteracoes):
    base = {
        "id_transacao": "TX_TESTE",
        "cliente": "Cliente Teste",
        "cpf": "12345678901",
        "idade": 30,
        "valor_bruto": 100.0,
        "categoria": "vestuario",
    }
    base.update(alteracoes)
    return base


# ---------------------------------------------------------------- validar_transacao

def test_transacao_valida_retorna_ok():
    assert validar_transacao(transacao()) == (True, "OK")


@pytest.mark.parametrize("valor, esperado", [
    (-50.0, False),   # partição inválida: negativo
    (-0.01, False),   # limite
    (0.0, False),     # limite exato: zero não é permitido
    (0.01, True),     # primeiro valor válido
    (1000.0, True),   # partição válida
])
def test_valor_bruto_limites(valor, esperado):
    valida, _ = validar_transacao(transacao(valor_bruto=valor))
    assert valida is esperado


@pytest.mark.parametrize("idade, esperado", [
    (-1, False),
    (0, True),
    (1, True),
    (119, True),
    (120, True),
    (121, False),
])
def test_idade_limites(idade, esperado):
    valida, _ = validar_transacao(transacao(idade=idade))
    assert valida is esperado


@pytest.mark.parametrize("cpf, esperado", [
    ("123", False),            # muito curto (caso TX1006)
    ("1234567890", False),     # 10 dígitos
    ("12345678901", True),     # 11 dígitos
    ("123456789012", False),   # 12 dígitos
    ("1234567890a", False),    # 11 caracteres com letra
    ("123.456.789", False),    # com pontuação
    ("", False),
])
def test_cpf_tamanho_e_formato(cpf, esperado):
    valida, _ = validar_transacao(transacao(cpf=cpf))
    assert valida is esperado


@pytest.mark.parametrize("campo, valor", [
    ("valor_bruto", None),
    ("valor_bruto", "100"),
    ("idade", None),
    ("idade", 30.5),
    ("cpf", None),
    ("cpf", 12345678901),
])
def test_tipos_invalidos_sao_rejeitados(campo, valor):
    valida, motivo = validar_transacao(transacao(**{campo: valor}))
    assert valida is False
    assert motivo


def test_motivo_de_falha_e_descritivo():
    valida, motivo = validar_transacao(transacao(valor_bruto=-50.0))
    assert valida is False
    assert "maior que zero" in motivo


@pytest.mark.parametrize("idade, esperado", [(17, False), (18, True)])
def test_menor_nao_compra_eletronicos(idade, esperado):
    valida, _ = validar_transacao(transacao(idade=idade, categoria="eletronicos"))
    assert valida is esperado


def test_menor_pode_comprar_outras_categorias():
    assert validar_transacao(transacao(idade=17, categoria="livros")) == (True, "OK")


# ---------------------------------------------------------- calcular_desconto_e_final

def test_sem_desconto():
    assert calcular_desconto_e_final(150.0, 25, "eletronicos") == (0.0, 150.0)


@pytest.mark.parametrize("idade, desconto, final", [
    (59, 0.0, 100.0),    # um ano antes do limite: sem desconto
    (60, 15.0, 85.0),    # limite exato: já é idoso
    (61, 15.0, 85.0),
])
def test_desconto_idoso_limite_59_60(idade, desconto, final):
    assert calcular_desconto_e_final(100.0, idade, "vestuario") == (desconto, final)


def test_desconto_livros():
    assert calcular_desconto_e_final(80.0, 17, "livros") == (8.0, 72.0)


def test_descontos_acumulam_ate_25_por_cento():
    # idoso (15%) + livros (10%) = 25%, exatamente o teto
    assert calcular_desconto_e_final(200.0, 65, "livros") == (50.0, 150.0)


def test_desconto_nunca_passa_de_25_por_cento(monkeypatch):
    import regra_negocio
    monkeypatch.setattr(regra_negocio, "DESCONTO_IDOSO", 0.20)
    # 20% + 10% = 30%, deve ser limitado a 25%
    assert regra_negocio.calcular_desconto_e_final(100.0, 70, "livros") == (25.0, 75.0)


def test_valor_com_centavos_e_arredondado():
    desconto, final = calcular_desconto_e_final(350.50, 60, "eletronicos")
    assert (desconto, final) == (52.58, 297.92)
    assert round(desconto + final, 2) == 350.50


def test_calculo_bloqueia_menor_em_eletronicos():
    with pytest.raises(ValueError):
        calcular_desconto_e_final(100.0, 17, "eletronicos")


# ------------------------------------------------- os 10 casos do arquivo de entrada

ARQUIVO_DADOS = Path(__file__).resolve().parent.parent / "dados_processamento.json"
RESULTADOS_ESPERADOS = {
    # id: (válida, valor_desconto, valor_final)
    "TX1001": (True, 0.0, 150.0),
    "TX1002": (True, 8.0, 72.0),
    "TX1003": (True, 75.0, 425.0),
    "TX1004": (True, 0.0, 200.0),
    "TX1005": (False, None, None),
    "TX1006": (False, None, None),
    "TX1007": (True, 150.0, 850.0),
    "TX1008": (False, None, None),
    "TX1009": (True, 0.0, 350.5),
    "TX10010": (True, 18.0, 102.0),
}


def carregar_dados():
    with open(ARQUIVO_DADOS, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def test_arquivo_tem_os_10_casos():
    ids = [t["id_transacao"] for t in carregar_dados()]
    assert ids == list(RESULTADOS_ESPERADOS)


@pytest.mark.parametrize("registro", carregar_dados(), ids=lambda t: t["id_transacao"])
def test_casos_do_json(registro):
    valida_esperada, desconto_esperado, final_esperado = RESULTADOS_ESPERADOS[registro["id_transacao"]]
    valida, _ = validar_transacao(registro)
    assert valida is valida_esperada
    if valida:
        resultado = calcular_desconto_e_final(registro["valor_bruto"], registro["idade"], registro["categoria"])
        assert resultado == (desconto_esperado, final_esperado)
