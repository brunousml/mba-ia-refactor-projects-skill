"""Configuração lida do ambiente uma vez, na importação."""
import logging
import os
import secrets

logger = logging.getLogger(__name__)

APP_ENV = os.environ.get("APP_ENV", "development")
EM_PRODUCAO = APP_ENV == "production"


def _flag(nome):
    return os.environ.get(nome, "false").strip().lower() in ("1", "true", "yes", "on")


def segredo(nome):
    valor = os.environ.get(nome)
    if valor:
        return valor
    if EM_PRODUCAO:
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {nome}")
    logger.warning("%s não definida; usando valor aleatório de desenvolvimento", nome)
    return secrets.token_hex(32)


SECRET_KEY = segredo("SECRET_KEY")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))
DEBUG = _flag("DEBUG")
DB_PATH = os.environ.get("DB_PATH", "loja.db")
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
VERSAO = "1.0.0"

# T08: rotas sensíveis ficam desligadas (403) até a flag ser ligada; ligadas, exigem X-Admin-Token.
ENABLE_ADMIN_ROUTES = _flag("ENABLE_ADMIN_ROUTES")
ENABLE_SENSITIVE_READS = _flag("ENABLE_SENSITIVE_READS")
ENABLE_WRITE_ROUTES = _flag("ENABLE_WRITE_ROUTES")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

if (ENABLE_ADMIN_ROUTES or ENABLE_SENSITIVE_READS or ENABLE_WRITE_ROUTES) and not ADMIN_TOKEN:
    if EM_PRODUCAO:
        raise RuntimeError("ADMIN_TOKEN é obrigatório quando alguma flag ENABLE_* está ligada")
    logger.warning("Flag ENABLE_* ligada sem ADMIN_TOKEN: as rotas protegidas responderão 401")
