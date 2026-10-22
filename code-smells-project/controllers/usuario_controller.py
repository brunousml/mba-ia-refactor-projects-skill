from flask import jsonify

from controllers.entrada import corpo_json
from middlewares.conexao import conexao_atual
from services import usuario_service


def _texto(dados, campo):
    valor = dados.get(campo, "")
    return valor if isinstance(valor, str) else ""


def listar_usuarios():
    return jsonify({"dados": usuario_service.listar(conexao_atual()), "sucesso": True}), 200


def buscar_usuario(id):
    return jsonify({"dados": usuario_service.buscar(conexao_atual(), id), "sucesso": True}), 200


def criar_usuario():
    dados = corpo_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    nome, email, senha = _texto(dados, "nome"), _texto(dados, "email"), _texto(dados, "senha")
    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400
    usuario_id = usuario_service.criar(conexao_atual(), nome, email, senha)
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    dados = corpo_json() or {}
    email, senha = _texto(dados, "email"), _texto(dados, "senha")
    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400
    usuario = usuario_service.autenticar(conexao_atual(), email, senha)
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
