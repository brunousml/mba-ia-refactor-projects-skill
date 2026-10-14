import logging
import os
import secrets

logger = logging.getLogger(__name__)

APP_ENV = os.environ.get("APP_ENV", "development")


def _segredo(nome):
    valor = os.environ.get(nome)
    if valor:
        return valor
    if APP_ENV == "production":
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {nome}")
    logger.warning("%s não definida; usando valor aleatório de desenvolvimento", nome)
    return secrets.token_hex(32)


def _flag(nome):
    return os.environ.get(nome, "false").lower() == "true"


SECRET_KEY = _segredo("SECRET_KEY")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))   # mesmo default do projeto original
DEBUG = _flag("DEBUG")
DB_PATH = os.environ.get("DB_PATH", "loja.db")
CORS_ORIGINS = [origem.strip() for origem in os.environ.get("CORS_ORIGINS", "*").split(",")]

# Rotas /admin/* ficam registradas, mas respondem 403 até a flag ser ligada; com ela, exigem X-Admin-Token.
ENABLE_ADMIN_ROUTES = _flag("ENABLE_ADMIN_ROUTES")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
