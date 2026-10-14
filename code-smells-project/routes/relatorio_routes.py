from controllers import relatorio_controller


def registrar(app):
    app.add_url_rule("/relatorios/vendas", "relatorio_vendas", relatorio_controller.relatorio_vendas, methods=["GET"])
