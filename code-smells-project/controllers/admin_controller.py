import logging

from flask import jsonify

from controllers.validadores import corpo_json
from services import admin_service

logger = logging.getLogger(__name__)


def reset_database():
    admin_service.resetar()
    logger.warning("Banco de dados resetado")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    dados = corpo_json()
    query = dados.get("sql", "") if isinstance(dados, dict) else ""
    if not query:
        return jsonify({"erro": "Query não informada"}), 400

    dados_consulta = admin_service.executar(query)
    if dados_consulta is not None:
        return jsonify({"dados": dados_consulta, "sucesso": True}), 200
    return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
