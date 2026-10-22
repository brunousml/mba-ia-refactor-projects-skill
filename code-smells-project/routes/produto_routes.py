from controllers import produto_controller as c
from middlewares.guards import exigir_escrita


def registrar(app):
    app.add_url_rule("/produtos", "listar_produtos", c.listar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/busca", "buscar_produtos", c.buscar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/<int:id>", "buscar_produto", c.buscar_produto, methods=["GET"])
    app.add_url_rule("/produtos", "criar_produto", exigir_escrita(c.criar_produto), methods=["POST"])
    app.add_url_rule("/produtos/<int:id>", "atualizar_produto", exigir_escrita(c.atualizar_produto), methods=["PUT"])
    app.add_url_rule("/produtos/<int:id>", "deletar_produto", exigir_escrita(c.deletar_produto), methods=["DELETE"])
