"""Relatório de vendas com desconto por faixa de faturamento."""
from config.regras import FAIXAS_DE_DESCONTO, STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE
from models import pedido_model


def calcular_desconto(faturamento):
    for limite, percentual in FAIXAS_DE_DESCONTO:
        if faturamento > limite:
            return faturamento * percentual
    return 0


def relatorio_vendas(conn):
    total_pedidos, faturamento, por_status = pedido_model.resumo_vendas(conn)
    faturamento = faturamento or 0
    desconto = calcular_desconto(faturamento)
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": por_status.get(STATUS_PENDENTE, 0),
        "pedidos_aprovados": por_status.get(STATUS_APROVADO, 0),
        "pedidos_cancelados": por_status.get(STATUS_CANCELADO, 0),
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
