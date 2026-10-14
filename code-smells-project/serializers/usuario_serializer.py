def usuario_publico(usuario):
    """Sem o campo senha."""
    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "tipo": usuario["tipo"],
        "criado_em": usuario["criado_em"],
    }


def usuario_login(usuario):
    return {"id": usuario["id"], "nome": usuario["nome"], "email": usuario["email"], "tipo": usuario["tipo"]}
