from flask import request

from services.errors import ValidationError


def json_body(allow_empty=False):
    """Corpo JSON como objeto; corpo ausente, nulo ou que não é objeto responde 400."""
    data = request.get_json()
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise ValidationError('Dados inválidos')
    return data
