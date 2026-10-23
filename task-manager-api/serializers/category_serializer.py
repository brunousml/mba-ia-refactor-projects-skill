def category_to_dict(c):
    return {
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'color': c.color,
        'created_at': str(c.created_at),
    }


def category_list_item(c, task_count):
    data = category_to_dict(c)
    data['task_count'] = task_count
    return data
