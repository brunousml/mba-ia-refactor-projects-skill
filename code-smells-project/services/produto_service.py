from models import produto_model


def listar():
    return produto_model.get_todos_produtos()


def buscar(id):
    return produto_model.get_produto_por_id(id)


def criar(nome, descricao, preco, estoque, categoria):
    return produto_model.criar_produto(nome, descricao, preco, estoque, categoria)


def atualizar(id, nome, descricao, preco, estoque, categoria):
    return produto_model.atualizar_produto(id, nome, descricao, preco, estoque, categoria)


def deletar(id):
    return produto_model.deletar_produto(id)


def buscar_com_filtros(termo, categoria, preco_min, preco_max):
    return produto_model.buscar_produtos(termo, categoria, preco_min, preco_max)
