from flask import jsonify, request

from middlewares.conexao import conexao_da_requisicao
from services import admin_service
from utils.tipos import eh_texto_preenchido


def reset_database():
    admin_service.resetar_banco(conexao_da_requisicao())
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    dados = request.get_json(silent=True)
    query = dados.get("sql", "") if isinstance(dados, dict) else ""
    if not eh_texto_preenchido(query):
        return jsonify({"erro": "Query não informada"}), 400
    linhas = admin_service.executar_sql(conexao_da_requisicao(), query)
    if linhas is not None:
        return jsonify({"dados": linhas, "sucesso": True}), 200
    return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
