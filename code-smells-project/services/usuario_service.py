"""Regras de usuário e autenticação."""
import logging

from config.regras import TIPO_USUARIO_PADRAO
from models import usuario_model
from serializers.usuario_serializer import usuario_autenticado, usuario_publico
from services.erros import ErroDeNegocio
from utils.senha import gerar_hash, verificar_senha

logger = logging.getLogger(__name__)


def listar(conn):
    return [usuario_publico(u) for u in usuario_model.listar(conn)]


def buscar(conn, usuario_id):
    usuario = usuario_model.buscar_por_id(conn, usuario_id)
    if usuario is None:
        raise ErroDeNegocio("Usuário não encontrado", 404)
    return usuario_publico(usuario)


def criar(conn, nome, email, senha):
    # O tipo nunca vem do cadastro público.
    usuario_id = usuario_model.criar(conn, nome, email, gerar_hash(senha), TIPO_USUARIO_PADRAO)
    logger.info("Usuário criado: id=%s", usuario_id)
    return usuario_id


def autenticar(conn, email, senha):
    usuario = usuario_model.buscar_por_email(conn, email)
    if usuario is None or not verificar_senha(senha, usuario["senha"]):
        logger.info("Login falhou")
        raise ErroDeNegocio("Email ou senha inválidos", 401, com_sucesso=True)
    logger.info("Login bem-sucedido: usuario_id=%s", usuario["id"])
    return usuario_autenticado(usuario)
