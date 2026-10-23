import logging

from flask import Flask
from flask_cors import CORS

from config import settings
from middlewares.erros import registrar_erros
from models.database import fechar_db, inicializar_banco
from routes import registrar_rotas

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = Flask(__name__)
app.config["SECRET_KEY"] = settings.SECRET_KEY
app.config["DEBUG"] = settings.DEBUG
CORS(app, origins=settings.CORS_ORIGINS)

registrar_rotas(app)
registrar_erros(app)
app.teardown_appcontext(fechar_db)

# Cria as tabelas e o seed antes de atender qualquer requisição.
inicializar_banco()

if __name__ == "__main__":
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print(f"Rodando em http://localhost:{settings.PORT}")
    print("=" * 50)

    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
