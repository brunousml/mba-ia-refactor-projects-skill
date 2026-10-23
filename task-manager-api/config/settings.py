"""Configuração lida do ambiente uma vez, no boot."""
import logging
import os
import secrets

logger = logging.getLogger(__name__)

APP_ENV = os.environ.get('APP_ENV', 'development')


def _flag(name):
    return os.environ.get(name, 'false').strip().lower() == 'true'


def _secret(name):
    value = os.environ.get(name)
    if value:
        return value
    if APP_ENV == 'production':
        raise RuntimeError(f'Variável de ambiente obrigatória ausente: {name}')
    logger.warning('%s não definida; usando valor aleatório de desenvolvimento', name)
    return secrets.token_hex(32)


SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
SECRET_KEY = _secret('SECRET_KEY')
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', '5000'))
DEBUG = _flag('DEBUG')
CORS_ORIGINS = [o.strip() for o in os.environ.get('CORS_ORIGINS', '').split(',') if o.strip()]

# Guards do T08: desligados por default (403); ligados exigem X-Admin-Token == ADMIN_TOKEN.
ENABLE_ADMIN_ROUTES = _flag('ENABLE_ADMIN_ROUTES')
ENABLE_SENSITIVE_READS = _flag('ENABLE_SENSITIVE_READS')
ENABLE_WRITE_ROUTES = _flag('ENABLE_WRITE_ROUTES')
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '')
if (ENABLE_ADMIN_ROUTES or ENABLE_SENSITIVE_READS or ENABLE_WRITE_ROUTES) and not ADMIN_TOKEN:
    if APP_ENV == 'production':
        raise RuntimeError('ADMIN_TOKEN é obrigatório quando uma flag ENABLE_* está ligada')
    logger.warning('Flag ENABLE_* ligada sem ADMIN_TOKEN: as rotas guardadas vão responder 401')
