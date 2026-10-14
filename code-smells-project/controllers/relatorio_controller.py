from flask import jsonify

from middlewares.conexao import conexao_da_requisicao
from services import relatorio_service


def relatorio_vendas():
    return jsonify({"dados": relatorio_service.relatorio_vendas(conexao_da_requisicao()), "sucesso": True}), 200
