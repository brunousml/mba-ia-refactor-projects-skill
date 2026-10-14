import logging
from datetime import datetime

from config.rules import (
    DEFAULT_PRIORITY, DUE_DATE_FORMAT, MAX_PRIORITY, MAX_TITLE_LENGTH, MIN_PRIORITY, MIN_TITLE_LENGTH,
    TAGS_SEPARATOR, TASK_STATUS_DONE, TASK_STATUS_PENDING, TASK_STATUSES,
)
from models import category as category_model
from models import task as task_model
from models import user as user_model
from models.task import Task
from services.errors import NotFoundError, ValidationError
from services.persistence import save
from services.stats import completion_rate
from utils.time import utcnow

logger = logging.getLogger(__name__)


# --- validação única de campos, usada pela criação e pela atualização ---

def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_title(title):
    if not isinstance(title, str):
        raise ValidationError('Título deve ser um texto')
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def _validate_status(status):
    if status not in TASK_STATUSES:
        raise ValidationError('Status inválido')
    return status


def _validate_priority(priority):
    if not _is_int(priority) or not MIN_PRIORITY <= priority <= MAX_PRIORITY:
        raise ValidationError(f'Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}')
    return priority


def _ensure_user_exists(user_id):
    if user_id and not user_model.find_by_id(user_id):
        raise NotFoundError('Usuário não encontrado')
    return user_id


def _ensure_category_exists(category_id):
    if category_id and not category_model.find_by_id(category_id):
        raise NotFoundError('Categoria não encontrada')
    return category_id


def _parse_due_date(value):
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError('Formato de data inválido. Use YYYY-MM-DD')


def _join_tags(tags):
    if isinstance(tags, list):
        if not all(isinstance(tag, str) for tag in tags):
            raise ValidationError('Tags inválidas')
        return TAGS_SEPARATOR.join(tags)
    if tags is not None and not isinstance(tags, str):
        raise ValidationError('Tags inválidas')
    return tags


# --- casos de uso ---

def list_tasks():
    return task_model.list_all_with_relations()


def get_task(task_id):
    task = task_model.find_by_id(task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return task


def create_task(data):
    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')

    task = Task()
    task.title = _validate_title(title)
    task.description = data.get('description', '')
    task.status = _validate_status(data.get('status', TASK_STATUS_PENDING))
    task.priority = _validate_priority(data.get('priority', DEFAULT_PRIORITY))
    task.user_id = _ensure_user_exists(data.get('user_id'))
    task.category_id = _ensure_category_exists(data.get('category_id'))
    if data.get('due_date'):
        task.due_date = _parse_due_date(data['due_date'])
    if data.get('tags'):
        task.tags = _join_tags(data['tags'])

    task_model.add(task)
    save('Erro ao criar task')
    logger.info('Task criada: id=%s', task.id)
    return task


def update_task(task_id, data):
    task = get_task(task_id)

    if 'title' in data:
        task.title = _validate_title(data['title'])
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        task.status = _validate_status(data['status'])
    if 'priority' in data:
        task.priority = _validate_priority(data['priority'])
    if 'user_id' in data:
        task.user_id = _ensure_user_exists(data['user_id'])
    if 'category_id' in data:
        task.category_id = _ensure_category_exists(data['category_id'])
    if 'due_date' in data:
        task.due_date = _parse_due_date(data['due_date']) if data['due_date'] else None
    if 'tags' in data:
        task.tags = _join_tags(data['tags'])
    task.updated_at = utcnow()

    save('Erro ao atualizar')
    logger.info('Task atualizada: id=%s', task.id)
    return task


def delete_task(task_id):
    task = get_task(task_id)
    task_model.delete(task)
    save('Erro ao deletar')
    logger.info('Task deletada: id=%s', task_id)


def _parse_int_filter(value, message):
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(message)


def search_tasks(text, status, priority, user_id):
    return task_model.search(
        text,
        status,
        _parse_int_filter(priority, 'Prioridade inválida'),
        _parse_int_filter(user_id, 'Usuário inválido'),
    )


def task_stats():
    total = task_model.count_all()
    by_status = task_model.count_by_status()
    now = utcnow()
    return {
        'total': total,
        **{status: by_status.get(status, 0) for status in TASK_STATUSES},
        'overdue': sum(1 for task in task_model.list_all() if task.is_overdue(now)),
        'completion_rate': completion_rate(by_status.get(TASK_STATUS_DONE, 0), total),
    }
