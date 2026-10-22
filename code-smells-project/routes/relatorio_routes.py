from controllers import relatorio_controller as c
from middlewares.guards import exigir_admin


def registrar(app):
    app.add_url_rule("/relatorios/vendas", "relatorio_vendas", exigir_admin(c.relatorio_vendas), methods=["GET"])
