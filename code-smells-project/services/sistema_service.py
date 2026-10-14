from config import settings
from config.regras import VERSAO_API
from models import pedido_model, produto_model, usuario_model


def health(conn):
    return {
        "status": "ok",
        "database": "connected",
        "counts": {
            "produtos": produto_model.contar(conn),
            "usuarios": usuario_model.contar(conn),
            "pedidos": pedido_model.contar(conn)
        },
        "versao": VERSAO_API,
        "ambiente": settings.APP_ENV
    }
