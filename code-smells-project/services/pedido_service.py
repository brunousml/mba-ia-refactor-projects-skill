import logging

from models import pedido_model, produto_model
from services.erros import ErroDominio

logger = logging.getLogger(__name__)

SEM_SUCESSO = {"sucesso": False}


def criar_pedido(usuario_id, itens):
    """Regra do pedido: há estoque para cada item, e o total é a soma dos itens.

    O contrato original não envia credencial do dono; o guard de escrita (T08) limita quem age.
    """
    total = 0
    for item in itens:
        produto = produto_model.get_produto_por_id(item["produto_id"])
        if produto is None:
            raise ErroDominio("Produto " + str(item["produto_id"]) + " não encontrado", 400, SEM_SUCESSO)
        if produto["estoque"] < item["quantidade"]:
            raise ErroDominio("Estoque insuficiente para " + produto["nome"], 400, SEM_SUCESSO)
        total = total + (produto["preco"] * item["quantidade"])

    pedido_id = pedido_model.inserir_pedido(usuario_id, total)
    for item in itens:
        produto = produto_model.get_produto_por_id(item["produto_id"])
        pedido_model.inserir_item(pedido_id, item["produto_id"], item["quantidade"], produto["preco"])
        produto_model.baixar_estoque(item["produto_id"], item["quantidade"])
    return {"pedido_id": pedido_id, "total": total}


def listar_do_usuario(usuario_id):
    return pedido_model.get_pedidos_usuario(usuario_id)


def listar_todos():
    return pedido_model.get_todos_pedidos()


def atualizar_status(pedido_id, novo_status):
    if not pedido_model.atualizar_status_pedido(pedido_id, novo_status):
        raise ErroDominio("Pedido não encontrado", 404, SEM_SUCESSO)
    if novo_status == "aprovado":
        logger.info("Pedido %s aprovado: preparar envio", pedido_id)
    if novo_status == "cancelado":
        logger.info("Pedido %s cancelado: devolver estoque", pedido_id)
