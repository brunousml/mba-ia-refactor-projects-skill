import logging
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from config import rules
from models import task as task_model
from models import user as user_model
from models import category as category_model
from models.task import Task
from services.errors import DomainError, NotFoundError
from utils.time import utc_now

logger = logging.getLogger(__name__)


def list_tasks():
    """Devolve (task, user_name, category_name) de cada task, com usuário e categoria carregados juntos."""
    return [
        (t, t.user.name if t.user else None, t.category.name if t.category else None)
        for t in task_model.list_all_with_relations()
    ]


def get_task(task_id):
    task = task_model.get_by_id(task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return task


def _validate_title(title):
    if len(title) < rules.MIN_TITLE_LENGTH:
        raise DomainError('Título muito curto')
    if len(title) > rules.MAX_TITLE_LENGTH:
        raise DomainError('Título muito longo')


def _validate_status(status):
    if status not in rules.TASK_STATUSES:
        raise DomainError('Status inválido')


def _validate_priority(priority):
    if priority < rules.MIN_PRIORITY or priority > rules.MAX_PRIORITY:
        raise DomainError('Prioridade deve ser entre 1 e 5')


def _check_user(user_id):
    if user_id and not user_model.get_by_id(user_id):
        raise NotFoundError('Usuário não encontrado')


def _check_category(category_id):
    if category_id and not category_model.get_by_id(category_id):
        raise NotFoundError('Categoria não encontrada')


def _parse_date(value, message):
    try:
        return datetime.strptime(value, rules.DATE_FORMAT)
    except ValueError:
        raise DomainError(message)


def _join_tags(tags):
    if isinstance(tags, list):
        return ','.join(tags)
    return tags


def _commit(action, message):
    try:
        action()
    except SQLAlchemyError:
        task_model.rollback()
        logger.exception(message)
        raise DomainError(message, 500)


def create_task(data):
    title = data.get('title')
    if not title:
        raise DomainError('Título é obrigatório')
    _validate_title(title)

    status = data.get('status', rules.DEFAULT_STATUS)
    priority = data.get('priority', rules.DEFAULT_PRIORITY)
    user_id = data.get('user_id')
    category_id = data.get('category_id')
    due_date = data.get('due_date')
    tags = data.get('tags')

    _validate_status(status)
    _validate_priority(priority)
    _check_user(user_id)
    _check_category(category_id)

    task = Task()
    task.title = title
    task.description = data.get('description', '')
    task.status = status
    task.priority = priority
    task.user_id = user_id
    task.category_id = category_id
    if due_date:
        task.due_date = _parse_date(due_date, 'Formato de data inválido. Use YYYY-MM-DD')
    if tags:
        task.tags = _join_tags(tags)

    _commit(lambda: task_model.add(task), 'Erro ao criar task')
    logger.info('Task criada: id=%s', task.id)
    return task


def update_task(task_id, data):
    task = get_task(task_id)

    if 'title' in data:
        _validate_title(data['title'])
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        _validate_status(data['status'])
        task.status = data['status']
    if 'priority' in data:
        _validate_priority(data['priority'])
        task.priority = data['priority']
    if 'user_id' in data:
        _check_user(data['user_id'])
        task.user_id = data['user_id']
    if 'category_id' in data:
        _check_category(data['category_id'])
        task.category_id = data['category_id']
    if 'due_date' in data:
        if data['due_date']:
            task.due_date = _parse_date(data['due_date'], 'Formato de data inválido')
        else:
            task.due_date = None
    if 'tags' in data:
        task.tags = _join_tags(data['tags'])

    task.updated_at = utc_now()
    _commit(task_model.save, 'Erro ao atualizar')
    logger.info('Task atualizada: id=%s', task.id)
    return task


def delete_task(task_id):
    task = get_task(task_id)
    _commit(lambda: task_model.delete(task), 'Erro ao deletar')
    logger.info('Task deletada: id=%s', task_id)


def search(text, status, priority, user_id):
    return task_model.search(text, status, priority, user_id)


def completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0


def stats():
    by_status = task_model.count_by(Task.status)
    total = sum(by_status.values())
    done = by_status.get('done', 0)
    now = utc_now()
    overdue_count = len([t for t in task_model.list_all() if t.is_overdue(now)])
    return {
        'total': total,
        'pending': by_status.get('pending', 0),
        'in_progress': by_status.get('in_progress', 0),
        'done': done,
        'cancelled': by_status.get('cancelled', 0),
        'overdue': overdue_count,
        'completion_rate': completion_rate(done, total),
    }
