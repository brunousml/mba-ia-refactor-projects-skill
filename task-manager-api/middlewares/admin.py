"""Proteção das rotas destrutivas e de relatório.

A API ainda não tem autenticação real (o token do /login não é verificado por ninguém).
Até existir, essas rotas ficam atrás de uma flag desligada por padrão e de um token de administração.
"""
import hmac
from functools import wraps

from flask import current_app, jsonify, request


def _admin_token_matches():
    expected = current_app.config.get('ADMIN_TOKEN', '')
    received = request.headers.get('X-Admin-Token', '')
    return bool(expected) and hmac.compare_digest(received, expected)


def is_admin_request():
    return current_app.config.get('ENABLE_ADMIN_ROUTES', False) and _admin_token_matches()


def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_app.config.get('ENABLE_ADMIN_ROUTES', False):
            return jsonify({'error': 'Recurso desabilitado'}), 403
        if not _admin_token_matches():
            return jsonify({'error': 'Não autorizado'}), 401
        return view(*args, **kwargs)
    return wrapped
