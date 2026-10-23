"""Guards do T08: a rota segue registrada, mas fica atrás de uma flag e do X-Admin-Token."""
import hmac
from functools import wraps

from flask import current_app, jsonify, request


def has_valid_admin_token():
    expected = current_app.config.get('ADMIN_TOKEN') or ''
    token = request.headers.get('X-Admin-Token', '')
    return bool(expected) and hmac.compare_digest(token.encode(), expected.encode())


def require_flag(flag_name):
    def decorator(handler):
        @wraps(handler)
        def wrapped(*args, **kwargs):
            if not current_app.config.get(flag_name):
                return jsonify({'error': 'Recurso desabilitado'}), 403
            if not has_valid_admin_token():
                return jsonify({'error': 'Não autorizado'}), 401
            return handler(*args, **kwargs)
        return wrapped
    return decorator


require_admin = require_flag('ENABLE_ADMIN_ROUTES')
require_sensitive_read = require_flag('ENABLE_SENSITIVE_READS')
require_write = require_flag('ENABLE_WRITE_ROUTES')
