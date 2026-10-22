"""Regras de pedido: total, estoque, status e notificações."""
import logging

from config.regras import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE, STATUS_VALIDOS
from models import pedido_model, produto_model
from serializers.pedido_serializer import pedido_publico
from services.erros import ErroDeNegocio

logger = logging.getLogger(__name__)


def criar_pedido(conn, usuario_id, itens):
    """Valida todos os itens antes de gravar; devolve {"pedido_id", "total"}."""
    produtos = produto_model.buscar_por_ids(conn, {item["produto_id"] for item in itens})
    total = 0
    for item in itens:
        produto = produtos.get(item["produto_id"])
        if produto is None:
            raise ErroDeNegocio("Produto " + str(item["produto_id"]) + " não encontrado", com_sucesso=True)
        if produto["estoque"] < item["quantidade"]:
            raise ErroDeNegocio("Estoque insuficiente para " + produto["nome"], com_sucesso=True)
        total = total + (produto["preco"] * item["quantidade"])

    pedido_id = pedido_model.criar(conn, usuario_id, STATUS_PENDENTE, total)
    for item in itens:
        preco = produtos[item["produto_id"]]["preco"]
        pedido_model.adicionar_item(conn, pedido_id, item["produto_id"], item["quantidade"], preco)
        produto_model.baixar_estoque(conn, item["produto_id"], item["quantidade"])

    _notificar_pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar(conn, usuario_id=None):
    return [pedido_publico(p) for p in pedido_model.listar_pedidos(conn, usuario_id)]


def atualizar_status(conn, pedido_id, novo_status):
    if novo_status not in STATUS_VALIDOS:
        raise ErroDeNegocio("Status inválido")
    pedido_model.atualizar_status(conn, pedido_id, novo_status)
    if novo_status == STATUS_APROVADO:
        logger.info("Notificação: pedido %s aprovado; preparar envio", pedido_id)
    if novo_status == STATUS_CANCELADO:
        logger.info("Notificação: pedido %s cancelado; devolver estoque", pedido_id)


def _notificar_pedido_criado(pedido_id, usuario_id):
    # Integrações de e-mail, SMS e push ainda são simuladas.
    logger.info("Notificação de pedido criado: pedido_id=%s usuario_id=%s", pedido_id, usuario_id)
