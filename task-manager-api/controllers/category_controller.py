from flask import jsonify

from controllers.request_body import json_body
from serializers.category_serializer import category_list_item, category_to_dict
from services import category_service


def list_categories():
    return jsonify([category_list_item(c, count) for c, count in category_service.list_categories()]), 200


def create_category():
    category = category_service.create_category(json_body())
    return jsonify(category_to_dict(category)), 201


def update_category(category_id):
    category_service.get_category(category_id)   # 404 antes de validar o corpo, como no original
    # O original aceitava corpo vazio ({}) sem alterar nada
    category = category_service.update_category(category_id, json_body(allow_empty=True))
    return jsonify(category_to_dict(category)), 200


def delete_category(category_id):
    category_service.delete_category(category_id)
    return jsonify({'message': 'Categoria deletada'}), 200
