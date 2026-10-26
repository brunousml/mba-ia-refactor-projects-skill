def usuario_publico(usuario):
    """Campos públicos de um usuário. O hash de senha nunca sai na resposta (T05)."""
    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "tipo": usuario["tipo"],
        "criado_em": usuario["criado_em"],
    }
