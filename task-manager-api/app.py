import logging

from flask import Flask
from flask_cors import CORS

from config import settings
from database import db
from middlewares.errors import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.system_routes import system_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['ENABLE_ADMIN_ROUTES'] = settings.ENABLE_ADMIN_ROUTES
    app.config['ENABLE_SENSITIVE_READS'] = settings.ENABLE_SENSITIVE_READS
    app.config['ENABLE_WRITE_ROUTES'] = settings.ENABLE_WRITE_ROUTES
    app.config['ADMIN_TOKEN'] = settings.ADMIN_TOKEN

    if settings.CORS_ORIGINS:
        CORS(app, origins=settings.CORS_ORIGINS)
    db.init_app(app)
    register_error_handlers(app)

    for blueprint in (task_bp, user_bp, report_bp, category_bp, system_bp):
        app.register_blueprint(blueprint)

    with app.app_context():
        db.create_all()
    return app


app = create_app()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    app.run(debug=settings.DEBUG, host=settings.HOST, port=settings.PORT)
