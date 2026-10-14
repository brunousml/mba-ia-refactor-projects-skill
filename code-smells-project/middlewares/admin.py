import hmac
from functools import wraps

from flask import jsonify, request

from config import settings


def exigir_admin(handler):
    """Rota administrativa: 403 com a flag desligada; com ela ligada, exige o header X-Admin-Token."""
    @wraps(handler)
    def envolvido(*args, **kwargs):
        if not settings.ENABLE_ADMIN_ROUTES:
            return jsonify({"erro": "Recurso desabilitado"}), 403
        token = request.headers.get("X-Admin-Token", "")
        if not settings.ADMIN_TOKEN or not hmac.compare_digest(token, settings.ADMIN_TOKEN):
            return jsonify({"erro": "Não autorizado"}), 401
        return handler(*args, **kwargs)
    return envolvido
