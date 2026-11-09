"""Ponto de entrada CLI: processa o lote de transações e grava no SQLite."""

import json
import logging
import sys
import time

import database
from regra_negocio import calcular_desconto_e_final, validar_transacao

ARQUIVO_ENTRADA = "dados_processamento.json"
ARQUIVO_LOG = "app.log"


def configurar_log() -> logging.Logger:
    logger = logging.getLogger("processamento")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formato = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%Y-%m-%d %H:%M:%S")
    for handler in (logging.FileHandler(ARQUIVO_LOG, encoding="utf-8"), logging.StreamHandler(sys.stdout)):
        handler.setFormatter(formato)
        logger.addHandler(handler)
    return logger


def processar_transacao(transacao: dict, logger: logging.Logger) -> bool:
    """Processa uma transação; retorna True se aprovada."""
    valida, motivo = validar_transacao(transacao)
    registro = dict(transacao)

    if valida:
        _, valor_final = calcular_desconto_e_final(
            transacao["valor_bruto"], transacao["idade"], transacao["categoria"]
        )
        registro.update(valor_final=valor_final, status="APROVADO", motivo_rejeicao=None)
        database.salvar_transacao(registro)
        logger.info("%s APROVADO | bruto=%.2f final=%.2f",
                    transacao["id_transacao"], transacao["valor_bruto"], valor_final)
        return True

    registro.update(valor_final=None, status="REJEITADO", motivo_rejeicao=motivo)
    database.salvar_transacao(registro)
    logger.warning("%s REJEITADO | %s", transacao.get("id_transacao"), motivo)
    return False


def main() -> int:
    logger = configurar_log()
    logger.info("Início do processamento em lote")
    inicio = time.perf_counter()

    try:
        with open(ARQUIVO_ENTRADA, encoding="utf-8") as arquivo:
            transacoes = json.load(arquivo)
        database.inicializar_banco()
    except (OSError, json.JSONDecodeError) as erro:
        logger.error("Falha ao preparar o processamento: %s", erro)
        return 1

    aprovados = rejeitados = 0
    for transacao in transacoes:
        try:
            if processar_transacao(transacao, logger):
                aprovados += 1
            else:
                rejeitados += 1
        except Exception as erro:  # um registro com erro não derruba o lote
            rejeitados += 1
            logger.error("%s ERRO inesperado: %s", transacao.get("id_transacao"), erro)

    tempo_ms = (time.perf_counter() - inicio) * 1000
    logger.info("Fim do processamento | total=%d aprovados=%d rejeitados=%d tempo=%.2f ms",
                len(transacoes), aprovados, rejeitados, tempo_ms)

    print("\n===== SUMÁRIO =====")
    print(f"Total processado: {len(transacoes)}")
    print(f"Aprovados:        {aprovados}")
    print(f"Rejeitados:       {rejeitados}")
    print(f"Tempo total:      {tempo_ms:.2f} ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
