from datetime import timedelta

from config import rules
from models import category as category_model
from models import task as task_model
from models import user as user_model
from models.task import Task
from services.errors import NotFoundError
from services.task_service import completion_rate
from utils.time import utc_now


def _overdue_entry(task, now):
    return {
        'id': task.id,
        'title': task.title,
        'due_date': str(task.due_date),
        'days_overdue': (now - task.due_date).days,
    }


def summary():
    now = utc_now()
    tasks = task_model.list_all()
    by_status = task_model.count_by(Task.status)
    by_priority = task_model.count_by(Task.priority)
    by_user = task_model.count_by(Task.user_id)
    done_by_user = task_model.count_done_by_user()
    overdue_list = [_overdue_entry(t, now) for t in tasks if t.is_overdue(now)]
    since = now - timedelta(days=rules.RECENT_ACTIVITY_DAYS)

    user_stats = []
    for u in user_model.list_all():
        total = by_user.get(u.id, 0)
        completed = done_by_user.get(u.id, 0)
        user_stats.append({
            'user_id': u.id,
            'user_name': u.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': completion_rate(completed, total),
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': len(tasks),
            'total_users': user_model.count(),
            'total_categories': category_model.count(),
        },
        'tasks_by_status': {status: by_status.get(status, 0) for status in rules.TASK_STATUSES},
        'tasks_by_priority': {label: by_priority.get(priority, 0)
                              for priority, label in rules.PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(overdue_list),
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': task_model.count_created_since(since),
            'tasks_completed_last_7_days': task_model.count_done_since(since),
        },
        'user_productivity': user_stats,
    }


def user_report(user_id):
    user = user_model.get_by_id(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')

    now = utc_now()
    tasks = task_model.list_by_user(user_id)
    counts = {status: 0 for status in rules.TASK_STATUSES}
    for t in tasks:
        if t.status in counts:
            counts[t.status] += 1

    return {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': len(tasks),
            'done': counts['done'],
            'pending': counts['pending'],
            'in_progress': counts['in_progress'],
            'cancelled': counts['cancelled'],
            'overdue': len([t for t in tasks if t.is_overdue(now)]),
            'high_priority': len([t for t in tasks if t.priority <= rules.HIGH_PRIORITY_MAX]),
            'completion_rate': completion_rate(counts['done'], len(tasks)),
        }
    }
