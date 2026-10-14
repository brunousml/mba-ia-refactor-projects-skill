from flask import jsonify, request

from middlewares.conexao import conexao_da_requisicao
from serializers.usuario_serializer import usuario_login, usuario_publico
from services import usuario_service
from utils.tipos import eh_texto_preenchido


def _corpo_json():
    dados = request.get_json(silent=True)
    return dados if isinstance(dados, dict) else None


def listar_usuarios():
    usuarios = usuario_service.listar(conexao_da_requisicao())
    return jsonify({"dados": [usuario_publico(u) for u in usuarios], "sucesso": True}), 200


def buscar_usuario(usuario_id):
    usuario = usuario_service.obter(conexao_da_requisicao(), usuario_id)
    return jsonify({"dados": usuario_publico(usuario), "sucesso": True}), 200


def criar_usuario():
    dados = _corpo_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not all(eh_texto_preenchido(campo) for campo in (nome, email, senha)):
        return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

    usuario_id = usuario_service.criar(conexao_da_requisicao(), nome, email, senha)
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    dados = _corpo_json()
    if dados is None:
        return jsonify({"erro": "Dados inválidos"}), 400

    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not eh_texto_preenchido(email) or not eh_texto_preenchido(senha):
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    usuario = usuario_service.autenticar(conexao_da_requisicao(), email, senha)
    return jsonify({"dados": usuario_login(usuario), "sucesso": True, "mensagem": "Login OK"}), 200
