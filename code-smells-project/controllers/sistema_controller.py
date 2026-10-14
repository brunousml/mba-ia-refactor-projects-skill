from flask import jsonify

from config.regras import VERSAO_API
from middlewares.conexao import conexao_da_requisicao
from services import sistema_service


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": VERSAO_API,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health"
        }
    })


def health_check():
    return jsonify(sistema_service.health(conexao_da_requisicao())), 200
