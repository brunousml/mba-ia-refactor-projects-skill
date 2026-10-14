from config.rules import ROLE_USER
from database import db
from models.task import Task, count_grouped_by
from utils.passwords import hash_password, verify_password
from utils.time import utcnow


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=ROLE_USER)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def set_password(self, plain_password):
        self.password = hash_password(plain_password)

    def check_password(self, plain_password):
        return verify_password(plain_password, self.password)


def find_by_id(user_id):
    return db.session.get(User, user_id)


def find_by_email(email):
    return User.query.filter_by(email=email).first()


def list_all():
    return User.query.order_by(User.id).all()


def list_with_task_count():
    counts = count_grouped_by(Task.user_id)
    return [(user, counts.get(user.id, 0)) for user in list_all()]


def count_all():
    return User.query.count()


def add(user):
    db.session.add(user)


def delete(user):
    db.session.delete(user)
