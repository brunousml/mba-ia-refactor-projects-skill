from controllers import sistema_controller


def registrar(app):
    app.add_url_rule("/", "index", sistema_controller.index, methods=["GET"])
    app.add_url_rule("/health", "health_check", sistema_controller.health_check, methods=["GET"])
