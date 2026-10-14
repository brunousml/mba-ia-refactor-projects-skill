import logging

from flask import Flask
from flask_cors import CORS

from config import settings
from middlewares import conexao, erros
from models.database import Banco
from routes import registrar_rotas


def create_app():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    banco = Banco(settings.DB_PATH)
    banco.inicializar()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    CORS(app, origins=settings.CORS_ORIGINS)
    conexao.registrar(app, banco)
    erros.registrar(app)
    registrar_rotas(app)
    return app


app = create_app()

if __name__ == "__main__":
    logging.getLogger(__name__).info("Servidor iniciado em http://localhost:%s", settings.PORT)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
