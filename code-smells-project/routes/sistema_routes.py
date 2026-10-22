from controllers import sistema_controller as c


def registrar(app):
    app.add_url_rule("/", "index", c.index, methods=["GET"])
    app.add_url_rule("/health", "health_check", c.health_check, methods=["GET"])
