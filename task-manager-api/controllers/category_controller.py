from flask import jsonify

from controllers.request_body import check_category_fields, json_body
from serializers.category_serializer import category_list_item, category_to_dict
from services import category_service


def list_categories():
    return jsonify([category_list_item(c, n) for c, n in category_service.list_categories()]), 200


def create_category():
    data = json_body()
    check_category_fields(data)
    return jsonify(category_to_dict(category_service.create_category(data))), 201


def update_category(cat_id):
    category_service.get_category(cat_id)
    data = json_body(allow_empty=True)
    check_category_fields(data)
    return jsonify(category_to_dict(category_service.update_category(cat_id, data))), 200


def delete_category(cat_id):
    category_service.delete_category(cat_id)
    return jsonify({'message': 'Categoria deletada'}), 200
