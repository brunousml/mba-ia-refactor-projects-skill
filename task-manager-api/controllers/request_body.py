"""Validação de formato na borda (T17): tipo errado vira 400, nunca 500."""
import re

from flask import request

from config import rules
from services.errors import DomainError


def json_body(allow_empty=False):
    """Corpo JSON como dict, ou 400 'Dados inválidos' (null, lista, escalar; {} se não permitido)."""
    data = request.get_json()
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise DomainError('Dados inválidos')
    return data


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _require_type(data, field, check, message):
    if field in data and not check(data[field]):
        raise DomainError(message)


def _is_optional_str(value):
    return value is None or isinstance(value, str)


def _is_tags(value):
    return value is None or isinstance(value, str) or (
        isinstance(value, list) and all(isinstance(t, str) for t in value))


def check_task_fields(data, creating):
    if creating and 'title' in data and not isinstance(data['title'], str):
        raise DomainError('Título é obrigatório')
    _require_type(data, 'title', lambda v: isinstance(v, str), 'Título deve ser texto')
    _require_type(data, 'description', _is_optional_str, 'Descrição deve ser texto')
    _require_type(data, 'status', lambda v: isinstance(v, str), 'Status inválido')
    _require_type(data, 'priority', _is_int, 'Prioridade deve ser entre 1 e 5')
    _require_type(data, 'user_id', lambda v: v is None or _is_int(v), 'user_id inválido')
    _require_type(data, 'category_id', lambda v: v is None or _is_int(v), 'category_id inválido')
    _require_type(data, 'due_date', _is_optional_str, 'Formato de data inválido')
    _require_type(data, 'tags', _is_tags, 'Tags inválidas')


def check_user_fields(data):
    _require_type(data, 'name', lambda v: isinstance(v, str), 'Nome deve ser texto')
    _require_type(data, 'email', lambda v: isinstance(v, str), 'Email inválido')
    _require_type(data, 'password', lambda v: isinstance(v, str), 'Senha deve ser texto')
    _require_type(data, 'role', lambda v: isinstance(v, str), 'Role inválido')
    _require_type(data, 'active', lambda v: isinstance(v, bool), 'active deve ser booleano')


def check_category_fields(data):
    _require_type(data, 'name', lambda v: isinstance(v, str), 'Nome deve ser texto')
    _require_type(data, 'description', _is_optional_str, 'Descrição deve ser texto')
    _require_type(data, 'color',
                  lambda v: isinstance(v, str) and re.match(rules.COLOR_PATTERN, v) is not None,
                  'Cor inválida. Use #RRGGBB')


def int_query_param(name):
    value = request.args.get(name, '')
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise DomainError(f'Parâmetro {name} inválido')
