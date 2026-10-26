from controllers import sistema_controller as ctl


def registrar(app):
    app.add_url_rule("/health", "health_check", ctl.health_check, methods=["GET"])
    app.add_url_rule("/", "index", ctl.index, methods=["GET"])
