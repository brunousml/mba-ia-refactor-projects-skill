import logging

from flask import jsonify

from controllers.validadores import corpo_json, validar_login, validar_usuario
from serializers.usuario_serializer import usuario_publico
from services import usuario_service

logger = logging.getLogger(__name__)


def listar_usuarios():
    usuarios = usuario_service.listar()
    return jsonify({"dados": [usuario_publico(u) for u in usuarios], "sucesso": True}), 200


def buscar_usuario(id):
    usuario = usuario_service.buscar(id)
    if usuario:
        return jsonify({"dados": usuario_publico(usuario), "sucesso": True}), 200
    return jsonify({"erro": "Usuário não encontrado"}), 404


def criar_usuario():
    dados = corpo_json()
    mensagem = validar_usuario(dados)
    if mensagem:
        return jsonify({"erro": mensagem}), 400

    novo_id = usuario_service.criar(dados["nome"], dados["email"], dados["senha"])
    logger.info("Usuário criado: id=%s", novo_id)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201


def login():
    dados = corpo_json()
    mensagem = validar_login(dados)
    if mensagem:
        return jsonify({"erro": mensagem}), 400

    usuario = usuario_service.autenticar(dados["email"], dados["senha"])
    if usuario:
        logger.info("Login bem-sucedido: usuario_id=%s", usuario["id"])
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
    logger.info("Login falhou")
    return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
