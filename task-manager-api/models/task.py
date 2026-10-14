from sqlalchemy import case, func
from sqlalchemy.orm import joinedload

from config.rules import CLOSED_TASK_STATUSES, DEFAULT_PRIORITY, TASK_STATUS_DONE, TASK_STATUS_PENDING
from database import db
from utils.time import utcnow


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=TASK_STATUS_PENDING)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date) and self.due_date < now and self.status not in CLOSED_TASK_STATUSES


def find_by_id(task_id):
    return db.session.get(Task, task_id)


def list_all():
    return Task.query.order_by(Task.id).all()


def list_all_with_relations():
    # Usuário e categoria vêm no mesmo SELECT (JOIN), não uma consulta por task
    return Task.query.options(joinedload(Task.user), joinedload(Task.category)).order_by(Task.id).all()


def list_by_user(user_id):
    return Task.query.filter_by(user_id=user_id).order_by(Task.id).all()


def search(text, status, priority, user_id):
    query = Task.query
    if text:
        pattern = f'%{text}%'   # valor passado como parâmetro pelo ORM, não concatenado no SQL
        query = query.filter(db.or_(Task.title.like(pattern), Task.description.like(pattern)))
    if status:
        query = query.filter(Task.status == status)
    if priority is not None:
        query = query.filter(Task.priority == priority)
    if user_id is not None:
        query = query.filter(Task.user_id == user_id)
    return query.order_by(Task.id).all()


def count_all():
    return Task.query.count()


def count_grouped_by(column):
    """{valor da coluna: quantidade} numa única consulta GROUP BY."""
    return dict(db.session.query(column, func.count(Task.id)).group_by(column).all())


def count_by_status():
    return count_grouped_by(Task.status)


def count_by_priority():
    return count_grouped_by(Task.priority)


def count_by_category():
    return count_grouped_by(Task.category_id)


def totals_by_user():
    """{user_id: (total, concluídas)} numa única consulta."""
    done = func.sum(case((Task.status == TASK_STATUS_DONE, 1), else_=0))
    rows = db.session.query(Task.user_id, func.count(Task.id), done).group_by(Task.user_id).all()
    return {user_id: (total, completed or 0) for user_id, total, completed in rows}


def count_created_since(moment):
    return Task.query.filter(Task.created_at >= moment).count()


def count_done_since(moment):
    return Task.query.filter(Task.status == TASK_STATUS_DONE, Task.updated_at >= moment).count()


def add(task):
    db.session.add(task)


def delete(task):
    db.session.delete(task)
