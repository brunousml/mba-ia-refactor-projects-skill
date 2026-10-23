from flask import jsonify, request

from controllers.request_body import check_task_fields, int_query_param, json_body
from serializers.task_serializer import task_detail, task_list_item, task_to_dict
from services import task_service


def list_tasks():
    result = [task_list_item(t, user_name, category_name)
              for t, user_name, category_name in task_service.list_tasks()]
    return jsonify(result), 200


def get_task(task_id):
    return jsonify(task_detail(task_service.get_task(task_id))), 200


def create_task():
    data = json_body()
    check_task_fields(data, creating=True)
    return jsonify(task_to_dict(task_service.create_task(data))), 201


def update_task(task_id):
    task_service.get_task(task_id)
    data = json_body()
    check_task_fields(data, creating=False)
    return jsonify(task_to_dict(task_service.update_task(task_id, data))), 200


def delete_task(task_id):
    task_service.delete_task(task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    results = task_service.search(
        request.args.get('q', ''),
        request.args.get('status', ''),
        int_query_param('priority'),
        int_query_param('user_id'),
    )
    return jsonify([task_to_dict(t) for t in results]), 200


def task_stats():
    return jsonify(task_service.stats()), 200
