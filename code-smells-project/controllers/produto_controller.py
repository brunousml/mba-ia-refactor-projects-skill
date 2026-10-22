from flask import jsonify, request

from controllers.entrada import corpo_json, numero_da_query
from middlewares.conexao import conexao_atual
from services import produto_service


def listar_produtos():
    return jsonify({"dados": produto_service.listar(conexao_atual()), "sucesso": True}), 200


def buscar_produto(id):
    return jsonify({"dados": produto_service.buscar(conexao_atual(), id), "sucesso": True}), 200


def buscar_produtos():
    resultados = produto_service.pesquisar(
        conexao_atual(),
        request.args.get("q", ""),
        request.args.get("categoria", None),
        numero_da_query("preco_min"),
        numero_da_query("preco_max"),
    )
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def criar_produto():
    produto_id = produto_service.criar(conexao_atual(), corpo_json())
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id):
    produto_service.atualizar(conexao_atual(), id, corpo_json())
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id):
    produto_service.deletar(conexao_atual(), id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
