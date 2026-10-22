def usuario_publico(linha):
    """Sem o campo senha."""
    return {
        "id": linha["id"],
        "nome": linha["nome"],
        "email": linha["email"],
        "tipo": linha["tipo"],
        "criado_em": linha["criado_em"],
    }


def usuario_autenticado(linha):
    return {"id": linha["id"], "nome": linha["nome"], "email": linha["email"], "tipo": linha["tipo"]}
