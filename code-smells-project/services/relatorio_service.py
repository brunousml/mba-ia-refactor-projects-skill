from config.regras import FAIXAS_DESCONTO
from models import pedido_model


def resumo_vendas():
    dados = pedido_model.resumo_vendas()
    faturamento = dados["faturamento"]
    total_pedidos = dados["total_pedidos"]

    desconto = 0
    for limite, taxa in FAIXAS_DESCONTO:
        if faturamento > limite:
            desconto = faturamento * taxa
            break

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": dados["pendentes"],
        "pedidos_aprovados": dados["aprovados"],
        "pedidos_cancelados": dados["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0
    }
