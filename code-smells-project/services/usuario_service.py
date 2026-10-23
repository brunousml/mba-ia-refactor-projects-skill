from models import usuario_model


def listar():
    return usuario_model.get_todos_usuarios()


def buscar(id):
    return usuario_model.get_usuario_por_id(id)


def criar(nome, email, senha):
    return usuario_model.criar_usuario(nome, email, senha)


def autenticar(email, senha):
    return usuario_model.login_usuario(email, senha)
