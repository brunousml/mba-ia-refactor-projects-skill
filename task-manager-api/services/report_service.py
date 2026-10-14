from datetime import timedelta

from config.rules import (
    HIGH_PRIORITY_THRESHOLD, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, TASK_STATUS_DONE, TASK_STATUSES,
)
from models import category as category_model
from models import task as task_model
from models import user as user_model
from services.errors import NotFoundError
from services.stats import completion_rate
from utils.time import utcnow


def _overdue_entry(task, now):
    return {
        'id': task.id,
        'title': task.title,
        'due_date': str(task.due_date),
        'days_overdue': (now - task.due_date).days,
    }


def _user_productivity():
    totals = task_model.totals_by_user()
    productivity = []
    for user in user_model.list_all():
        total, completed = totals.get(user.id, (0, 0))
        productivity.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': completion_rate(completed, total),
        })
    return productivity


def summary_report():
    now = utcnow()
    by_status = task_model.count_by_status()
    by_priority = task_model.count_by_priority()
    overdue = [_overdue_entry(task, now) for task in task_model.list_all() if task.is_overdue(now)]
    recent_since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

    return {
        'generated_at': str(utcnow()),
        'overview': {
            'total_tasks': task_model.count_all(),
            'total_users': user_model.count_all(),
            'total_categories': category_model.count_all(),
        },
        'tasks_by_status': {status: by_status.get(status, 0) for status in TASK_STATUSES},
        'tasks_by_priority': {label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(overdue),
            'tasks': overdue,
        },
        'recent_activity': {
            'tasks_created_last_7_days': task_model.count_created_since(recent_since),
            'tasks_completed_last_7_days': task_model.count_done_since(recent_since),
        },
        'user_productivity': _user_productivity(),
    }


def user_report(user_id):
    user = user_model.find_by_id(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')

    now = utcnow()
    tasks = task_model.list_by_user(user_id)
    by_status = {status: 0 for status in TASK_STATUSES}
    for task in tasks:
        if task.status in by_status:
            by_status[task.status] += 1

    return {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': len(tasks),
            **by_status,
            'overdue': sum(1 for task in tasks if task.is_overdue(now)),
            'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_THRESHOLD),
            'completion_rate': completion_rate(by_status[TASK_STATUS_DONE], len(tasks)),
        },
    }
