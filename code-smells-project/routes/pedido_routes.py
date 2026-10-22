from controllers import pedido_controller as c
from middlewares.guards import exigir_escrita, exigir_leitura_sensivel


def registrar(app):
    app.add_url_rule("/pedidos", "criar_pedido", exigir_escrita(c.criar_pedido), methods=["POST"])
    app.add_url_rule("/pedidos", "listar_todos_pedidos", exigir_leitura_sensivel(c.listar_todos_pedidos), methods=["GET"])
    app.add_url_rule(
        "/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario",
        exigir_leitura_sensivel(c.listar_pedidos_usuario), methods=["GET"],
    )
    app.add_url_rule(
        "/pedidos/<int:pedido_id>/status", "atualizar_status_pedido",
        exigir_escrita(c.atualizar_status_pedido), methods=["PUT"],
    )
