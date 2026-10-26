from config import rules
from database import db
from utils.passwords import hash_password, verify_password
from utils.time import utc_now


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # hash com salt, nunca o texto
    role = db.Column(db.String(50), default=rules.DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def set_password(self, password):
        self.password = hash_password(password)

    def check_password(self, password):
        return verify_password(password, self.password)


def get_by_id(user_id):
    return db.session.get(User, user_id)


def get_by_email(email):
    return User.query.filter_by(email=email).first()


def list_all():
    return User.query.order_by(User.id).all()


def count():
    return User.query.count()


def add(user):
    db.session.add(user)
    db.session.commit()


def delete_with_tasks(user, tasks):
    for task in tasks:
        db.session.delete(task)
    db.session.delete(user)
    db.session.commit()


def save():
    db.session.commit()


def rollback():
    db.session.rollback()
