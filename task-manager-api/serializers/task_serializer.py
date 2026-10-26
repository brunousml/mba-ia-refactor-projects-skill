def task_to_dict(t):
    return {
        'id': t.id,
        'title': t.title,
        'description': t.description,
        'status': t.status,
        'priority': t.priority,
        'user_id': t.user_id,
        'category_id': t.category_id,
        'created_at': str(t.created_at),
        'updated_at': str(t.updated_at),
        'due_date': str(t.due_date) if t.due_date else None,
        'tags': t.tags.split(',') if t.tags else [],
    }


def task_detail(t):
    data = task_to_dict(t)
    data['overdue'] = t.is_overdue()
    return data


def task_list_item(t, user_name, category_name):
    data = task_detail(t)
    data['user_name'] = user_name
    data['category_name'] = category_name
    return data


def user_task_item(t):
    return {
        'id': t.id,
        'title': t.title,
        'description': t.description,
        'status': t.status,
        'priority': t.priority,
        'created_at': str(t.created_at),
        'due_date': str(t.due_date) if t.due_date else None,
        'overdue': t.is_overdue(),
    }
