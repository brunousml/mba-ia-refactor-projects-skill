"""Configuração lida do ambiente, validada no boot (T01, T08, T18)."""
import logging
import os
import secrets

logger = logging.getLogger(__name__)

APP_ENV = os.environ.get("APP_ENV", "development")


def _booleano(nome):
    return os.environ.get(nome, "false").strip().lower() == "true"


def _segredo(nome):
    valor = os.environ.get(nome)
    if valor:
        return valor
    if APP_ENV == "production":
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {nome}")
    logger.warning("%s não definida; usando valor aleatório de desenvolvimento", nome)
    return secrets.token_hex(32)


SECRET_KEY = _segredo("SECRET_KEY")
DEBUG = _booleano("DEBUG")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))  # mesmo default do projeto original
DB_PATH = os.environ.get("DB_PATH", "loja.db")
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]

ENABLE_ADMIN_ROUTES = _booleano("ENABLE_ADMIN_ROUTES")
ENABLE_SENSITIVE_READS = _booleano("ENABLE_SENSITIVE_READS")
ENABLE_WRITE_ROUTES = _booleano("ENABLE_WRITE_ROUTES")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

if (ENABLE_ADMIN_ROUTES or ENABLE_SENSITIVE_READS or ENABLE_WRITE_ROUTES) and not ADMIN_TOKEN:
    raise RuntimeError("ADMIN_TOKEN é obrigatório quando alguma flag ENABLE_* está ligada")
