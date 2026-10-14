from controllers import admin_controller
from middlewares.admin import exigir_admin


def registrar(app):
    app.add_url_rule("/admin/reset-db", "reset_database", exigir_admin(admin_controller.reset_database), methods=["POST"])
    app.add_url_rule("/admin/query", "executar_query", exigir_admin(admin_controller.executar_query), methods=["POST"])
