def produto_publico(linha):
    return {
        "id": linha["id"],
        "nome": linha["nome"],
        "descricao": linha["descricao"],
        "preco": linha["preco"],
        "estoque": linha["estoque"],
        "categoria": linha["categoria"],
        "ativo": linha["ativo"],
        "criado_em": linha["criado_em"],
    }
