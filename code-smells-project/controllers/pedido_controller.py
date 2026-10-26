import logging

from flask import jsonify

from controllers.validadores import corpo_json, validar_pedido, validar_status
from services import pedido_service

logger = logging.getLogger(__name__)


def criar_pedido():
    dados = corpo_json()
    mensagem = validar_pedido(dados)
    if mensagem:
        return jsonify({"erro": mensagem}), 400

    resultado = pedido_service.criar_pedido(dados["usuario_id"], dados["itens"])
    logger.info("Pedido %s criado: notificações simuladas (e-mail, SMS, push)", resultado["pedido_id"])

    return jsonify({
        "dados": resultado,
        "sucesso": True,
        "mensagem": "Pedido criado com sucesso"
    }), 201


def listar_pedidos_usuario(usuario_id):
    pedidos = pedido_service.listar_do_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos_pedidos():
    pedidos = pedido_service.listar_todos()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = corpo_json()
    mensagem = validar_status(dados)
    if mensagem:
        return jsonify({"erro": mensagem}), 400

    pedido_service.atualizar_status(pedido_id, dados["status"])
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
