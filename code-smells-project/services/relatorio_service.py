from config.regras import FAIXAS_DE_DESCONTO
from models import pedido_model


def desconto_por_faturamento(faturamento):
    for limite, taxa in FAIXAS_DE_DESCONTO:
        if faturamento > limite:
            return faturamento * taxa
    return 0


def relatorio_vendas(conn):
    totais = pedido_model.totais_de_vendas(conn)
    total_pedidos = totais["total_pedidos"]
    faturamento = totais["faturamento"] or 0
    desconto = desconto_por_faturamento(faturamento)

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": totais["pendentes"],
        "pedidos_aprovados": totais["aprovados"],
        "pedidos_cancelados": totais["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0
    }
