"""Lógica pura de negócio: validação e cálculo de descontos.

Este módulo não acessa banco de dados, arquivos ou rede. Todas as funções
são puras (mesma entrada -> mesma saída), o que facilita os testes unitários.
"""

from decimal import ROUND_HALF_UP, Decimal

CENTAVO = Decimal("0.01")

IDADE_MINIMA = 0
IDADE_MAXIMA = 120
TAMANHO_CPF = 11

IDADE_MAIORIDADE = 18
IDADE_IDOSO = 60
CATEGORIA_RESTRITA_MENORES = "eletronicos"

DESCONTO_IDOSO = 0.15
DESCONTO_LIVROS = 0.10
DESCONTO_MAXIMO = 0.25


def validar_transacao(transacao: dict) -> tuple[bool, str]:
    """Valida uma transação e retorna (True, "OK") ou (False, motivo)."""
    valor_bruto = transacao.get("valor_bruto")
    idade = transacao.get("idade")
    cpf = transacao.get("cpf")
    categoria = transacao.get("categoria")

    if not isinstance(valor_bruto, (int, float)) or isinstance(valor_bruto, bool):
        return False, "Valor bruto ausente ou não numérico"
    if valor_bruto <= 0:
        return False, f"Valor bruto deve ser maior que zero (recebido: {valor_bruto})"

    if not isinstance(idade, int) or isinstance(idade, bool):
        return False, "Idade ausente ou não inteira"
    if not IDADE_MINIMA <= idade <= IDADE_MAXIMA:
        return False, f"Idade fora do intervalo {IDADE_MINIMA}-{IDADE_MAXIMA} (recebido: {idade})"

    if not isinstance(cpf, str) or len(cpf) != TAMANHO_CPF or not cpf.isdigit():
        return False, f"CPF deve conter exatamente {TAMANHO_CPF} dígitos numéricos"

    if idade < IDADE_MAIORIDADE and categoria == CATEGORIA_RESTRITA_MENORES:
        return False, "Menores de 18 anos não podem comprar na categoria 'eletronicos'"

    return True, "OK"


def calcular_desconto_e_final(valor_bruto: float, idade: int, categoria: str) -> tuple[float, float]:
    """Calcula (valor_desconto, valor_final) aplicando as regras de desconto.

    - Idosos (>= 60 anos): 15% de desconto em qualquer categoria.
    - Categoria 'livros': 10% de desconto.
    - Descontos são somados, limitados a 25%.
    - Menores de 18 anos não podem comprar 'eletronicos' (levanta ValueError).
    """
    if idade < IDADE_MAIORIDADE and categoria == CATEGORIA_RESTRITA_MENORES:
        raise ValueError("Menores de 18 anos não podem comprar na categoria 'eletronicos'")

    percentual = 0.0
    if idade >= IDADE_IDOSO:
        percentual += DESCONTO_IDOSO
    if categoria == "livros":
        percentual += DESCONTO_LIVROS
    percentual = min(percentual, DESCONTO_MAXIMO)

    # Decimal evita erros de ponto flutuante (ex.: 350.50 * 0.15 = 52.575 -> 52.58)
    bruto = Decimal(str(valor_bruto))
    desconto = (bruto * Decimal(str(percentual))).quantize(CENTAVO, rounding=ROUND_HALF_UP)
    final = bruto - desconto
    return float(desconto), float(final)
