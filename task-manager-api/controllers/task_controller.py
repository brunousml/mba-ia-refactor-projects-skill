from flask import jsonify, request

from controllers.request_body import json_body
from serializers.task_serializer import task_detail, task_list_item, task_to_dict
from services import task_service
from utils.time import utcnow


def list_tasks():
    now = utcnow()
    return jsonify([task_list_item(task, task.is_overdue(now)) for task in task_service.list_tasks()]), 200


def get_task(task_id):
    task = task_service.get_task(task_id)
    return jsonify(task_detail(task, task.is_overdue())), 200


def create_task():
    task = task_service.create_task(json_body())
    return jsonify(task_to_dict(task)), 201


def update_task(task_id):
    task_service.get_task(task_id)   # 404 antes de validar o corpo, como no original
    task = task_service.update_task(task_id, json_body())
    return jsonify(task_to_dict(task)), 200


def delete_task(task_id):
    task_service.delete_task(task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    tasks = task_service.search_tasks(
        request.args.get('q', ''),
        request.args.get('status', ''),
        request.args.get('priority', ''),
        request.args.get('user_id', ''),
    )
    return jsonify([task_to_dict(task) for task in tasks]), 200


def task_stats():
    return jsonify(task_service.task_stats()), 200
