"""Configuração lida do ambiente (e do arquivo .env, se existir) uma única vez, no boot."""
import logging
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

APP_ENV = os.environ.get('APP_ENV', 'development')
IS_PRODUCTION = APP_ENV == 'production'


def _flag(name, default='false'):
    return os.environ.get(name, default).strip().lower() in ('1', 'true', 'yes', 'on')


def _secret(name):
    value = os.environ.get(name)
    if value:
        return value
    if IS_PRODUCTION:
        raise RuntimeError(f'Variável de ambiente obrigatória ausente: {name}')
    logger.warning('%s não definida; usando valor aleatório de desenvolvimento', name)
    return secrets.token_hex(32)


def _cors_origins():
    raw = os.environ.get('CORS_ORIGINS', '').strip()
    if not raw:
        # Em desenvolvimento mantém o comportamento original (qualquer origem);
        # em produção, sem lista explícita, o CORS fica desligado.
        return [] if IS_PRODUCTION else ['*']
    return [origin.strip() for origin in raw.split(',') if origin.strip()]


SECRET_KEY = _secret('SECRET_KEY')
DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///tasks.db')
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', '5000'))
DEBUG = _flag('DEBUG')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
CORS_ORIGINS = _cors_origins()

# Rotas destrutivas e de relatório ficam desligadas por padrão (403).
# Ligadas, exigem o cabeçalho X-Admin-Token igual a ADMIN_TOKEN.
ENABLE_ADMIN_ROUTES = _flag('ENABLE_ADMIN_ROUTES')
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '')
