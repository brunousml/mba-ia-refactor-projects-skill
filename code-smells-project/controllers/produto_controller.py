from flask import jsonify, request

from middlewares.conexao import conexao_da_requisicao
from serializers.produto_serializer import produto_publico
from services import produto_service
from services.erros import ErroDeNegocio


def _corpo_json():
    dados = request.get_json(silent=True)
    return dados if isinstance(dados, dict) else None


def _preco_da_query(nome):
    valor = request.args.get(nome, None)
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError:
        raise ErroDeNegocio(f"{nome} deve ser numérico")


def listar_produtos():
    produtos = produto_service.listar(conexao_da_requisicao())
    return jsonify({"dados": [produto_publico(p) for p in produtos], "sucesso": True}), 200


def buscar_produto(produto_id):
    produto = produto_service.obter(conexao_da_requisicao(), produto_id, sucesso_no_erro=False)
    return jsonify({"dados": produto_publico(produto), "sucesso": True}), 200


def criar_produto():
    dados = _corpo_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    produto_id = produto_service.criar(conexao_da_requisicao(), dados)
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(produto_id):
    produto_service.atualizar(conexao_da_requisicao(), produto_id, _corpo_json())
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(produto_id):
    produto_service.deletar(conexao_da_requisicao(), produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = _preco_da_query("preco_min")
    preco_max = _preco_da_query("preco_max")
    resultados = produto_service.buscar(conexao_da_requisicao(), termo, categoria, preco_min, preco_max)
    return jsonify({"dados": [produto_publico(p) for p in resultados], "total": len(resultados), "sucesso": True}), 200
