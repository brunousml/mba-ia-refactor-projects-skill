from flask import jsonify

from config import rules
from controllers.request_body import check_user_fields, json_body
from middlewares.guards import has_valid_admin_token
from serializers.task_serializer import task_to_dict, user_task_item
from serializers.user_serializer import user_list_item, user_to_dict
from services import user_service


def list_users():
    return jsonify([user_list_item(u, n) for u, n in user_service.list_users()]), 200


def get_user(user_id):
    user = user_service.get_user(user_id)
    data = user_to_dict(user)
    data['tasks'] = [task_to_dict(t) for t in user_service.user_tasks(user_id)]
    return jsonify(data), 200


def create_user():
    data = json_body()
    check_user_fields(data)
    user = user_service.create_user(data, requester_is_admin=has_valid_admin_token())
    return jsonify(user_to_dict(user)), 201


def update_user(user_id):
    user_service.get_user(user_id)
    data = json_body()
    check_user_fields(data)
    user = user_service.update_user(user_id, data, requester_is_admin=has_valid_admin_token())
    return jsonify(user_to_dict(user)), 200


def delete_user(user_id):
    user_service.delete_user(user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    return jsonify([user_task_item(t) for t in user_service.user_tasks(user_id)]), 200


def login():
    data = json_body()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({'error': 'Credenciais inválidas'}), 401
    user = user_service.login(email, password)
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user_to_dict(user),
        'token': rules.FAKE_TOKEN_PREFIX + str(user.id)
    }), 200
