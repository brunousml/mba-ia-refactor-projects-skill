from flask import jsonify

from services import relatorio_service


def relatorio_vendas():
    relatorio = relatorio_service.resumo_vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200
