from flask import jsonify, request

from middlewares.conexao import conexao_da_requisicao
from serializers.pedido_serializer import pedido_publico
from services import pedido_service
from utils.tipos import eh_inteiro


def _corpo_json():
    dados = request.get_json(silent=True)
    return dados if isinstance(dados, dict) else None


def _item_valido(item):
    return (
        isinstance(item, dict)
        and eh_inteiro(item.get("produto_id"))
        and eh_inteiro(item.get("quantidade"))
        and item["quantidade"] > 0
    )


def criar_pedido():
    dados = _corpo_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        return jsonify({"erro": "Usuario ID é obrigatório"}), 400
    if not eh_inteiro(usuario_id):
        return jsonify({"erro": "Usuario ID deve ser um número inteiro"}), 400
    if not itens:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400
    if not isinstance(itens, list) or not all(_item_valido(item) for item in itens):
        return jsonify({"erro": "Cada item precisa de produto_id e quantidade inteiros, com quantidade maior que zero"}), 400

    resultado = pedido_service.criar(conexao_da_requisicao(), usuario_id, itens)
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar_pedidos_usuario(usuario_id):
    pedidos = pedido_service.listar_por_usuario(conexao_da_requisicao(), usuario_id)
    return jsonify({"dados": [pedido_publico(p) for p in pedidos], "sucesso": True}), 200


def listar_todos_pedidos():
    pedidos = pedido_service.listar_todos(conexao_da_requisicao())
    return jsonify({"dados": [pedido_publico(p) for p in pedidos], "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = _corpo_json() or {}
    pedido_service.atualizar_status(conexao_da_requisicao(), pedido_id, dados.get("status", ""))
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
