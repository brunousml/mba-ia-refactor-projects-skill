"""Guards de acesso por flag (T08). Flag desligada: 403. Ligada sem token certo: 401."""
import hmac
from functools import wraps

from flask import jsonify, request

from config import settings


def exigir_flag(nome_flag):
    def decorador(handler):
        @wraps(handler)
        def envolvido(*args, **kwargs):
            if not getattr(settings, nome_flag):
                return jsonify({"erro": "Recurso desabilitado"}), 403
            token = request.headers.get("X-Admin-Token", "")
            if not settings.ADMIN_TOKEN or not hmac.compare_digest(token.encode(), settings.ADMIN_TOKEN.encode()):
                return jsonify({"erro": "Não autorizado"}), 401
            return handler(*args, **kwargs)

        return envolvido

    return decorador


exigir_admin = exigir_flag("ENABLE_ADMIN_ROUTES")
exigir_leitura_sensivel = exigir_flag("ENABLE_SENSITIVE_READS")
exigir_escrita = exigir_flag("ENABLE_WRITE_ROUTES")
