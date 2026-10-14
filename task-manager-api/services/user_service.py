import logging
import re

from config.rules import EMAIL_PATTERN, FAKE_TOKEN_PREFIX, MIN_PASSWORD_LENGTH, ROLE_USER, VALID_ROLES
from models import task as task_model
from models import user as user_model
from models.user import User
from services.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from services.persistence import save

logger = logging.getLogger(__name__)


def _require_text(value, missing_message, type_message):
    if not value:
        raise ValidationError(missing_message)
    if not isinstance(value, str):
        raise ValidationError(type_message)
    return value


def _validate_email_format(email):
    if not isinstance(email, str) or not re.match(EMAIL_PATTERN, email):
        raise ValidationError('Email inválido')
    return email


def _ensure_email_available(email, current_user_id=None):
    existing = user_model.find_by_email(email)
    if existing and existing.id != current_user_id:
        raise ConflictError('Email já cadastrado')


def _validate_role(role, current_role, can_grant_roles):
    if role not in VALID_ROLES:
        raise ValidationError('Role inválido')
    # Sem autenticação real, só o caminho administrativo escolhe um papel diferente do atual
    if role != current_role and not can_grant_roles:
        raise ForbiddenError('Sem permissão para definir role')
    return role


def list_users():
    return user_model.list_with_task_count()


def get_user(user_id):
    user = user_model.find_by_id(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return user


def list_user_tasks(user_id):
    get_user(user_id)
    return task_model.list_by_user(user_id)


def create_user(data, can_grant_roles=False):
    name = _require_text(data.get('name'), 'Nome é obrigatório', 'Nome deve ser um texto')
    email = _require_text(data.get('email'), 'Email é obrigatório', 'Email inválido')
    password = _require_text(data.get('password'), 'Senha é obrigatória', 'Senha deve ser um texto')
    _validate_email_format(email)
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
    _ensure_email_available(email)
    role = _validate_role(data.get('role', ROLE_USER), ROLE_USER, can_grant_roles)

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role

    user_model.add(user)
    save('Erro ao criar usuário')
    logger.info('Usuário criado: id=%s', user.id)
    return user


def update_user(user_id, data, can_grant_roles=False):
    user = get_user(user_id)

    if 'name' in data:
        if not isinstance(data['name'], str):
            raise ValidationError('Nome deve ser um texto')
        user.name = data['name']

    if 'email' in data:
        _validate_email_format(data['email'])
        _ensure_email_available(data['email'], current_user_id=user_id)
        user.email = data['email']

    if 'password' in data:
        if not isinstance(data['password'], str):
            raise ValidationError('Senha deve ser um texto')
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha muito curta')
        user.set_password(data['password'])

    if 'role' in data:
        user.role = _validate_role(data['role'], user.role, can_grant_roles)

    if 'active' in data:
        active = data['active']
        if not isinstance(active, bool) and active not in (0, 1):
            raise ValidationError('active deve ser booleano')
        user.active = bool(active)

    save('Erro ao atualizar')
    return user


def delete_user(user_id):
    user = get_user(user_id)
    # As tasks do usuário são apagadas junto (comportamento original)
    for task in task_model.list_by_user(user_id):
        task_model.delete(task)
    user_model.delete(user)
    save('Erro ao deletar')
    logger.info('Usuário deletado: id=%s', user_id)


def authenticate(email, password):
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    if not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError('Email e senha devem ser texto')
    user = user_model.find_by_email(email)
    if not user or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')
    return user, FAKE_TOKEN_PREFIX + str(user.id)
