from routes import admin_routes, pedido_routes, produto_routes, relatorio_routes, sistema_routes, usuario_routes

MODULOS = (produto_routes, usuario_routes, pedido_routes, relatorio_routes, sistema_routes, admin_routes)


def registrar_rotas(app):
    for modulo in MODULOS:
        modulo.registrar(app)
