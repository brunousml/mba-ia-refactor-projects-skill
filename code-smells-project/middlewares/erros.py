"""T10: handler central. Erros HTTP do Flask passam como estão; o resto vira JSON."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from middlewares.conexao import desfazer_requisicao
from services.erros import ErroDeNegocio

logger = logging.getLogger(__name__)


def registrar_erros(app):
    @app.errorhandler(Exception)
    def tratar_erro(erro):
        if isinstance(erro, HTTPException):
            return erro
        desfazer_requisicao()  # escrita parcial não é gravada
        if isinstance(erro, ErroDeNegocio):
            return jsonify(erro.corpo()), erro.status
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
