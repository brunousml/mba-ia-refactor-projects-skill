from controllers import usuario_controller as ctl
from middlewares.guards import exigir_escrita, exigir_leitura_sensivel


def registrar(app):
    app.add_url_rule("/usuarios", "listar_usuarios", exigir_leitura_sensivel(ctl.listar_usuarios), methods=["GET"])
    app.add_url_rule("/usuarios/<int:id>", "buscar_usuario", exigir_leitura_sensivel(ctl.buscar_usuario), methods=["GET"])
    app.add_url_rule("/usuarios", "criar_usuario", exigir_escrita(ctl.criar_usuario), methods=["POST"])
    app.add_url_rule("/login", "login", ctl.login, methods=["POST"])
