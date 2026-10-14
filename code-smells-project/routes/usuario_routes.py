from controllers import usuario_controller


def registrar(app):
    app.add_url_rule("/usuarios", "listar_usuarios", usuario_controller.listar_usuarios, methods=["GET"])
    app.add_url_rule("/usuarios/<int:usuario_id>", "buscar_usuario", usuario_controller.buscar_usuario, methods=["GET"])
    app.add_url_rule("/usuarios", "criar_usuario", usuario_controller.criar_usuario, methods=["POST"])
    app.add_url_rule("/login", "login", usuario_controller.login, methods=["POST"])
