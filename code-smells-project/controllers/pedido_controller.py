from flask import jsonify

from controllers.entrada import corpo_json
from middlewares.conexao import conexao_atual
from services import pedido_service
from utils.tipos import eh_inteiro


def _item_valido(item):
    return (
        isinstance(item, dict)
        and eh_inteiro(item.get("produto_id"))
        and eh_inteiro(item.get("quantidade"))
        and item["quantidade"] > 0
    )


def criar_pedido():
    dados = corpo_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        return jsonify({"erro": "Usuario ID é obrigatório"}), 400
    if not eh_inteiro(usuario_id):
        return jsonify({"erro": "Usuario ID deve ser inteiro"}), 400
    if not itens or not isinstance(itens, list):
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400
    if not all(_item_valido(item) for item in itens):
        return jsonify({"erro": "Cada item precisa de produto_id inteiro e quantidade inteira maior que zero"}), 400

    resultado = pedido_service.criar_pedido(conexao_atual(), usuario_id, itens)
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar_todos_pedidos():
    return jsonify({"dados": pedido_service.listar(conexao_atual()), "sucesso": True}), 200


def listar_pedidos_usuario(usuario_id):
    return jsonify({"dados": pedido_service.listar(conexao_atual(), usuario_id), "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = corpo_json() or {}
    pedido_service.atualizar_status(conexao_atual(), pedido_id, dados.get("status", ""))
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
