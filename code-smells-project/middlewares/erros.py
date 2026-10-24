"""Tratamento de erro central (T10). Erro de domínio vira a resposta dele; erro HTTP do framework
passa sem mudança; qualquer outra falha vira 500 com mensagem genérica e log completo no servidor."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from models.database import desfazer_transacao
from services.erros import ErroDominio

logger = logging.getLogger(__name__)


def registrar_erros(app):
    @app.errorhandler(ErroDominio)
    def erro_de_dominio(erro):
        desfazer_transacao()
        corpo = {"erro": str(erro)}
        corpo.update(erro.corpo_extra)
        return jsonify(corpo), erro.status

    @app.errorhandler(HTTPException)
    def erro_http(erro):
        return erro

    @app.errorhandler(Exception)
    def erro_interno(erro):
        desfazer_transacao()
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno"}), 500
