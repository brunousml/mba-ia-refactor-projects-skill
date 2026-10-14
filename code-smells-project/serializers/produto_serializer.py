CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def produto_publico(produto):
    return {campo: produto[campo] for campo in CAMPOS}
