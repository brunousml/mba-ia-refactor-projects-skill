from config.rules import DEFAULT_COLOR
from database import db
from models.task import count_by_category
from utils.time import utcnow


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)


def find_by_id(category_id):
    return db.session.get(Category, category_id)


def list_all():
    return Category.query.order_by(Category.id).all()


def list_with_task_count():
    counts = count_by_category()
    return [(category, counts.get(category.id, 0)) for category in list_all()]


def count_all():
    return Category.query.count()


def add(category):
    db.session.add(category)


def delete(category):
    db.session.delete(category)
