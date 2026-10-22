from flask import jsonify

from middlewares.conexao import conexao_atual
from services import relatorio_service


def relatorio_vendas():
    return jsonify({"dados": relatorio_service.relatorio_vendas(conexao_atual()), "sucesso": True}), 200
