import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from services.erros import ErroDeNegocio

logger = logging.getLogger(__name__)


def tratar_erro(erro):
    if isinstance(erro, HTTPException):
        return erro   # 404/405 nativos continuam como o Flask responde
    if isinstance(erro, ErroDeNegocio):
        corpo = {"erro": str(erro)}
        if erro.sucesso is not None:
            corpo["sucesso"] = erro.sucesso
        return jsonify(corpo), erro.status
    logger.exception("Erro não tratado")
    return jsonify({"erro": "Erro interno"}), 500   # detalhe só no log


def registrar(app):
    app.register_error_handler(Exception, tratar_erro)
