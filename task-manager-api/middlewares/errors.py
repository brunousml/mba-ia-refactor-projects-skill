"""Tratamento de erro central (T10)."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from services.errors import DomainError

logger = logging.getLogger(__name__)


def handle_domain_error(error):
    return jsonify({'error': str(error)}), error.status


def handle_unexpected_error(error):
    if isinstance(error, HTTPException):
        return error  # 404/405/415 do framework seguem como antes
    logger.exception('Erro não tratado')
    return jsonify({'error': 'Erro interno'}), 500


def register_error_handlers(app):
    app.register_error_handler(DomainError, handle_domain_error)
    app.register_error_handler(Exception, handle_unexpected_error)
