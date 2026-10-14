import logging

from config.regras import STATUS_APROVADO, STATUS_CANCELADO, STATUS_VALIDOS
from models import pedido_model
from services.erros import ErroDeNegocio

logger = logging.getLogger(__name__)


def criar(conn, usuario_id, itens):
    produtos = pedido_model.buscar_produtos(conn, [item["produto_id"] for item in itens])
    total = 0
    for item in itens:
        produto = produtos.get(item["produto_id"])
        if produto is None:
            raise ErroDeNegocio("Produto " + str(item["produto_id"]) + " não encontrado", sucesso=False)
        if produto["estoque"] < item["quantidade"]:
            raise ErroDeNegocio("Estoque insuficiente para " + produto["nome"], sucesso=False)
        total = total + (produto["preco"] * item["quantidade"])

    pedido_id = pedido_model.inserir_pedido(conn, usuario_id, total)
    for item in itens:
        pedido_model.inserir_item_e_baixar_estoque(
            conn, pedido_id, item["produto_id"], item["quantidade"], produtos[item["produto_id"]]["preco"]
        )
    conn.commit()   # pedido, itens e baixa de estoque na mesma transação

    # Notificações ainda são simuladas: só registram o evento.
    logger.info("Pedido criado: pedido_id=%s usuario_id=%s (notificações de e-mail/SMS/push pendentes)", pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar_por_usuario(conn, usuario_id):
    return pedido_model.listar_por_usuario(conn, usuario_id)


def listar_todos(conn):
    return pedido_model.listar_todos(conn)


def atualizar_status(conn, pedido_id, novo_status):
    if novo_status not in STATUS_VALIDOS:
        raise ErroDeNegocio("Status inválido")
    if not pedido_model.existe(conn, pedido_id):
        raise ErroDeNegocio("Pedido não encontrado", 404)
    pedido_model.atualizar_status(conn, pedido_id, novo_status)
    conn.commit()
    if novo_status == STATUS_APROVADO:
        logger.info("Pedido aprovado, preparar envio: pedido_id=%s", pedido_id)
    if novo_status == STATUS_CANCELADO:
        # O original só avisava "Devolver estoque" sem devolver; o comportamento foi mantido.
        logger.info("Pedido cancelado: pedido_id=%s", pedido_id)
