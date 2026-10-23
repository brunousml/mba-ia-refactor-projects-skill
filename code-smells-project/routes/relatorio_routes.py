from controllers import relatorio_controller as ctl
from middlewares.guards import exigir_leitura_sensivel


def registrar(app):
    app.add_url_rule("/relatorios/vendas", "relatorio_vendas", exigir_leitura_sensivel(ctl.relatorio_vendas), methods=["GET"])
