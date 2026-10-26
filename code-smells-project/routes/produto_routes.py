from controllers import produto_controller as ctl
from middlewares.guards import exigir_escrita


def registrar(app):
    app.add_url_rule("/produtos", "listar_produtos", ctl.listar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/busca", "buscar_produtos", ctl.buscar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/<int:id>", "buscar_produto", ctl.buscar_produto, methods=["GET"])
    app.add_url_rule("/produtos", "criar_produto", exigir_escrita(ctl.criar_produto), methods=["POST"])
    app.add_url_rule("/produtos/<int:id>", "atualizar_produto", exigir_escrita(ctl.atualizar_produto), methods=["PUT"])
    app.add_url_rule("/produtos/<int:id>", "deletar_produto", exigir_escrita(ctl.deletar_produto), methods=["DELETE"])
