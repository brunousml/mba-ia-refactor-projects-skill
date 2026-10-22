from flask import jsonify

from middlewares.conexao import conexao_atual
from services import sistema_service


def index():
    return jsonify(sistema_service.info_api())


def health_check():
    return jsonify(sistema_service.health(conexao_atual())), 200
