from flask import jsonify

from controllers.request_body import json_body
from middlewares.admin import is_admin_request
from serializers.task_serializer import task_to_dict, user_task_item
from serializers.user_serializer import user_list_item, user_to_dict
from services import user_service
from utils.time import utcnow


def list_users():
    return jsonify([user_list_item(user, count) for user, count in user_service.list_users()]), 200


def get_user(user_id):
    user = user_service.get_user(user_id)
    data = user_to_dict(user)
    data['tasks'] = [task_to_dict(task) for task in user_service.list_user_tasks(user_id)]
    return jsonify(data), 200


def create_user():
    user = user_service.create_user(json_body(), can_grant_roles=is_admin_request())
    return jsonify(user_to_dict(user)), 201


def update_user(user_id):
    user_service.get_user(user_id)   # 404 antes de validar o corpo, como no original
    user = user_service.update_user(user_id, json_body(), can_grant_roles=is_admin_request())
    return jsonify(user_to_dict(user)), 200


def delete_user(user_id):
    user_service.delete_user(user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def list_user_tasks(user_id):
    now = utcnow()
    tasks = user_service.list_user_tasks(user_id)
    return jsonify([user_task_item(task, task.is_overdue(now)) for task in tasks]), 200


def login():
    data = json_body()
    user, token = user_service.authenticate(data.get('email'), data.get('password'))
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user_to_dict(user),
        'token': token,
    }), 200
