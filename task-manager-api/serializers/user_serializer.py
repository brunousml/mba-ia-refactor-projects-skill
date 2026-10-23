def user_to_dict(u):
    """Campos públicos do usuário. A senha (hash) nunca sai na resposta."""
    return {
        'id': u.id,
        'name': u.name,
        'email': u.email,
        'role': u.role,
        'active': u.active,
        'created_at': str(u.created_at),
    }


def user_list_item(u, task_count):
    data = user_to_dict(u)
    data['task_count'] = task_count
    return data
