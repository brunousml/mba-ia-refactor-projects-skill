import logging
import re

from sqlalchemy.exc import SQLAlchemyError

from config import rules
from models import user as user_model
from models import task as task_model
from models.task import Task
from models.user import User
from services.errors import ConflictError, DomainError, NotFoundError

logger = logging.getLogger(__name__)


def list_users():
    """Devolve (user, quantidade de tasks) de cada usuário."""
    counts = task_model.count_by(Task.user_id)
    return [(u, counts.get(u.id, 0)) for u in user_model.list_all()]


def get_user(user_id):
    user = user_model.get_by_id(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return user


def user_tasks(user_id):
    get_user(user_id)
    return task_model.list_by_user(user_id)


def _validate_email_format(email):
    if not re.match(rules.EMAIL_PATTERN, email):
        raise DomainError('Email inválido')


def _validate_role(role, requester_is_admin):
    if role not in rules.USER_ROLES:
        raise DomainError('Role inválido')
    # Só um requisitante administrador define papel diferente do padrão (AP-15).
    if role != rules.DEFAULT_ROLE and not requester_is_admin:
        raise DomainError('Sem permissão para definir papel', 403)


def _commit(action, message):
    try:
        action()
    except SQLAlchemyError:
        user_model.rollback()
        logger.exception(message)
        raise DomainError(message, 500)


def create_user(data, requester_is_admin=False):
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', rules.DEFAULT_ROLE)

    if not name:
        raise DomainError('Nome é obrigatório')
    if not email:
        raise DomainError('Email é obrigatório')
    if not password:
        raise DomainError('Senha é obrigatória')
    _validate_email_format(email)
    if len(password) < rules.MIN_PASSWORD_LENGTH:
        raise DomainError('Senha deve ter no mínimo 4 caracteres')
    if user_model.get_by_email(email):
        raise ConflictError('Email já cadastrado')
    _validate_role(role, requester_is_admin)

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role

    _commit(lambda: user_model.add(user), 'Erro ao criar usuário')
    logger.info('Usuário criado: id=%s', user.id)
    return user


def update_user(user_id, data, requester_is_admin=False):
    user = get_user(user_id)

    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        _validate_email_format(data['email'])
        existing = user_model.get_by_email(data['email'])
        if existing and existing.id != user_id:
            raise ConflictError('Email já cadastrado')
        user.email = data['email']
    if 'password' in data:
        if len(data['password']) < rules.MIN_PASSWORD_LENGTH:
            raise DomainError('Senha muito curta')
        user.set_password(data['password'])
    if 'role' in data:
        _validate_role(data['role'], requester_is_admin)
        user.role = data['role']
    if 'active' in data:
        user.active = data['active']

    _commit(user_model.save, 'Erro ao atualizar')
    return user


def delete_user(user_id):
    user = get_user(user_id)
    tasks = task_model.list_by_user(user_id)
    _commit(lambda: user_model.delete_with_tasks(user, tasks), 'Erro ao deletar')
    logger.info('Usuário deletado: id=%s', user_id)


def login(email, password):
    user = user_model.get_by_email(email)
    if not user or not user.check_password(password):
        raise DomainError('Credenciais inválidas', 401)
    if not user.active:
        raise DomainError('Usuário inativo', 403)
    return user
