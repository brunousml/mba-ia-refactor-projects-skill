"""Informações públicas da API e health check (sem segredos)."""
from config import settings
from models import pedido_model, produto_model, usuario_model


def info_api():
    return {
        "mensagem": "Bem-vindo à API da Loja",
        "versao": settings.VERSAO,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    }


def health(conn):
    return {
        "status": "ok",
        "database": "connected",
        "counts": {
            "produtos": produto_model.contar(conn),
            "usuarios": usuario_model.contar(conn),
            "pedidos": pedido_model.contar(conn),
        },
        "versao": settings.VERSAO,
        "ambiente": settings.APP_ENV,
        "db_path": settings.DB_PATH,
        "debug": settings.DEBUG,
    }
