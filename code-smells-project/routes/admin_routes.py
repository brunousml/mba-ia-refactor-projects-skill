from controllers import admin_controller as c
from middlewares.guards import exigir_admin


def registrar(app):
    app.add_url_rule("/admin/reset-db", "reset_database", exigir_admin(c.reset_database), methods=["POST"])
    app.add_url_rule("/admin/query", "executar_query", exigir_admin(c.executar_query), methods=["POST"])
