import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

import database
from services.errors import AppError

logger = logging.getLogger(__name__)


def handle_error(error):
    # Erros HTTP do próprio Flask (404 de rota, 405, 415) seguem como o framework responde
    if isinstance(error, HTTPException):
        return error
    if isinstance(error, AppError):
        return jsonify({'error': error.message}), error.status
    database.rollback()
    logger.exception('Erro não tratado')
    return jsonify({'error': 'Erro interno'}), 500   # detalhe só no log


def register_error_handlers(app):
    app.register_error_handler(Exception, handle_error)
