from flask import Blueprint

from controllers import user_controller
from middlewares.guards import require_admin, require_sensitive_read, require_write

user_bp = Blueprint('users', __name__)

user_bp.add_url_rule('/users', view_func=require_sensitive_read(user_controller.list_users), methods=['GET'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=require_sensitive_read(user_controller.get_user), methods=['GET'])
user_bp.add_url_rule('/users', view_func=require_write(user_controller.create_user), methods=['POST'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=require_write(user_controller.update_user), methods=['PUT'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=require_admin(user_controller.delete_user), methods=['DELETE'])
user_bp.add_url_rule('/users/<int:user_id>/tasks', view_func=user_controller.get_user_tasks, methods=['GET'])
user_bp.add_url_rule('/login', view_func=user_controller.login, methods=['POST'])
