from flask import jsonify

from controllers.entrada import corpo_json
from middlewares.conexao import conexao_atual
from services import admin_service


def reset_database():
    admin_service.resetar_banco(conexao_atual())
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    dados = corpo_json() or {}
    query = dados.get("sql", "")
    if not query or not isinstance(query, str):
        return jsonify({"erro": "Query não informada"}), 400
    linhas = admin_service.executar_sql(conexao_atual(), query)
    if linhas is not None:
        return jsonify({"dados": linhas, "sucesso": True}), 200
    return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
