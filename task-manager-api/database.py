from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def commit():
    db.session.commit()


def rollback():
    db.session.rollback()
