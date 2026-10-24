from controllers import relatorio_controller as ctl
from middlewares.guards import exigir_admin


def registrar(app):
    app.add_url_rule("/relatorios/vendas", "relatorio_vendas", exigir_admin(ctl.relatorio_vendas), methods=["GET"])
