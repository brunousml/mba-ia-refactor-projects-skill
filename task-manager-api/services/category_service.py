import re

from config.rules import COLOR_PATTERN, DEFAULT_COLOR
from models import category as category_model
from models.category import Category
from services.errors import NotFoundError, ValidationError
from services.persistence import save


def _validate_name(name):
    if not isinstance(name, str):
        raise ValidationError('Nome deve ser um texto')
    return name


def _validate_color(color):
    if not isinstance(color, str) or not re.match(COLOR_PATTERN, color):
        raise ValidationError('Cor inválida. Use o formato #RRGGBB')
    return color


def list_categories():
    return category_model.list_with_task_count()


def get_category(category_id):
    category = category_model.find_by_id(category_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')
    return category


def create_category(data):
    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')

    category = Category()
    category.name = _validate_name(name)
    category.description = data.get('description', '')
    category.color = _validate_color(data.get('color', DEFAULT_COLOR))

    category_model.add(category)
    save('Erro ao criar categoria')
    return category


def update_category(category_id, data):
    category = get_category(category_id)
    if 'name' in data:
        category.name = _validate_name(data['name'])
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = _validate_color(data['color'])

    save('Erro ao atualizar')
    return category


def delete_category(category_id):
    category = get_category(category_id)
    category_model.delete(category)
    save('Erro ao deletar')
