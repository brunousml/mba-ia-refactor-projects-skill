import logging

from flask import jsonify, request

from controllers.validadores import converter_preco, corpo_json, validar_produto
from services import produto_service

logger = logging.getLogger(__name__)


def listar_produtos():
    produtos = produto_service.listar()
    logger.info("Listando %s produtos", len(produtos))
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(id):
    produto = produto_service.buscar(id)
    if produto:
        return jsonify({"dados": produto, "sucesso": True}), 200
    return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404


def criar_produto():
    dados = corpo_json()
    mensagem = validar_produto(dados)
    if mensagem:
        return jsonify({"erro": mensagem}), 400

    novo_id = produto_service.criar(
        dados["nome"], dados.get("descricao", ""), dados["preco"], dados["estoque"], dados.get("categoria", "geral")
    )
    logger.info("Produto criado: id=%s", novo_id)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id):
    if produto_service.buscar(id) is None:
        return jsonify({"erro": "Produto não encontrado"}), 404

    dados = corpo_json()
    mensagem = validar_produto(dados)
    if mensagem:
        return jsonify({"erro": mensagem}), 400

    produto_service.atualizar(
        id, dados["nome"], dados.get("descricao", ""), dados["preco"], dados["estoque"], dados.get("categoria", "geral")
    )
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id):
    if produto_service.buscar(id) is None:
        return jsonify({"erro": "Produto não encontrado"}), 404

    produto_service.deletar(id)
    logger.info("Produto deletado: id=%s", id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = converter_preco(request.args.get("preco_min", None), "preco_min")
    preco_max = converter_preco(request.args.get("preco_max", None), "preco_max")

    resultados = produto_service.buscar_com_filtros(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
