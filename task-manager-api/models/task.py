from sqlalchemy import func
from sqlalchemy.orm import joinedload

from config import rules
from database import db
from utils.time import utc_now


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=rules.DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=rules.DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def is_overdue(self, now=None):
        """Regra única de atraso: prazo vencido e task ainda aberta."""
        return (
            bool(self.due_date)
            and self.due_date < (now or utc_now())
            and self.status not in rules.CLOSED_STATUSES
        )


def get_by_id(task_id):
    return db.session.get(Task, task_id)


def list_all():
    return Task.query.order_by(Task.id).all()


def list_all_with_relations():
    return (Task.query
            .options(joinedload(Task.user), joinedload(Task.category))
            .order_by(Task.id)
            .all())


def list_by_user(user_id):
    return Task.query.filter_by(user_id=user_id).order_by(Task.id).all()


def count_by(column):
    """{valor da coluna: quantidade} numa única consulta GROUP BY."""
    rows = db.session.query(column, func.count(Task.id)).group_by(column).all()
    return {value: total for value, total in rows}


def count_done_by_user():
    rows = (db.session.query(Task.user_id, func.count(Task.id))
            .filter(Task.status == 'done')
            .group_by(Task.user_id)
            .all())
    return {user_id: total for user_id, total in rows}


def count_created_since(since):
    return Task.query.filter(Task.created_at >= since).count()


def count_done_since(since):
    return Task.query.filter(Task.status == 'done', Task.updated_at >= since).count()


def search(text=None, status=None, priority=None, user_id=None):
    tasks = Task.query
    if text:
        pattern = f'%{text}%'  # valor vai como parâmetro do LIKE, não concatenado no SQL
        tasks = tasks.filter(db.or_(Task.title.like(pattern), Task.description.like(pattern)))
    if status:
        tasks = tasks.filter(Task.status == status)
    if priority is not None:
        tasks = tasks.filter(Task.priority == priority)
    if user_id is not None:
        tasks = tasks.filter(Task.user_id == user_id)
    return tasks.order_by(Task.id).all()


def add(task):
    db.session.add(task)
    db.session.commit()


def delete(task):
    db.session.delete(task)
    db.session.commit()


def save():
    db.session.commit()


def rollback():
    db.session.rollback()
