import logging

from sqlalchemy.exc import SQLAlchemyError

from config import rules
from models import category as category_model
from models import task as task_model
from models.category import Category
from models.task import Task
from services.errors import DomainError, NotFoundError

logger = logging.getLogger(__name__)


def list_categories():
    """Devolve (categoria, quantidade de tasks) de cada categoria."""
    counts = task_model.count_by(Task.category_id)
    return [(c, counts.get(c.id, 0)) for c in category_model.list_all()]


def get_category(category_id):
    category = category_model.get_by_id(category_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')
    return category


def _commit(action, message):
    try:
        action()
    except SQLAlchemyError:
        category_model.rollback()
        logger.exception(message)
        raise DomainError(message, 500)


def create_category(data):
    name = data.get('name')
    if not name:
        raise DomainError('Nome é obrigatório')

    category = Category()
    category.name = name
    category.description = data.get('description', '')
    category.color = data.get('color', rules.DEFAULT_COLOR)

    _commit(lambda: category_model.add(category), 'Erro ao criar categoria')
    return category


def update_category(category_id, data):
    category = get_category(category_id)
    for field in ('name', 'description', 'color'):
        if field in data:
            setattr(category, field, data[field])
    _commit(category_model.save, 'Erro ao atualizar')
    return category


def delete_category(category_id):
    category = get_category(category_id)
    _commit(lambda: category_model.delete(category), 'Erro ao deletar')
