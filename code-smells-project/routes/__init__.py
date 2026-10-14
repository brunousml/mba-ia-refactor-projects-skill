from routes import admin_routes, pedido_routes, produto_routes, relatorio_routes, sistema_routes, usuario_routes


def registrar_rotas(app):
    for modulo in (produto_routes, usuario_routes, pedido_routes, relatorio_routes, sistema_routes, admin_routes):
        modulo.registrar(app)
