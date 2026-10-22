"""Entry point: compõe a aplicação a partir da config, do banco, dos middlewares e das rotas."""
import logging

from flask import Flask
from flask_cors import CORS

from config import settings
from middlewares.conexao import registrar_conexao
from middlewares.erros import registrar_erros
from models.database import Banco
from routes import registrar_rotas

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    if settings.CORS_ORIGINS:
        CORS(app, origins=settings.CORS_ORIGINS)

    banco = Banco(settings.DB_PATH)
    banco.inicializar()

    registrar_conexao(app, banco)
    registrar_erros(app)
    registrar_rotas(app)
    return app


if __name__ == "__main__":
    aplicacao = create_app()
    logger.info("Servidor iniciado em http://%s:%s (debug=%s)", settings.HOST, settings.PORT, settings.DEBUG)
    aplicacao.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
