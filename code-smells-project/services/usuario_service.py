import logging

from models import usuario_model
from services.erros import ErroDeNegocio
from utils.senha import gerar_hash, verificar_senha

logger = logging.getLogger(__name__)


def listar(conn):
    return usuario_model.listar(conn)


def obter(conn, usuario_id):
    usuario = usuario_model.buscar_por_id(conn, usuario_id)
    if usuario is None:
        raise ErroDeNegocio("Usuário não encontrado", 404)
    return usuario


def criar(conn, nome, email, senha):
    usuario_id = usuario_model.criar(conn, nome, email, gerar_hash(senha))
    conn.commit()
    logger.info("Usuário criado: usuario_id=%s", usuario_id)
    return usuario_id


def autenticar(conn, email, senha):
    usuario = usuario_model.buscar_por_email(conn, email)
    if usuario is None or not verificar_senha(senha, usuario["senha"]):
        logger.info("Login falhou")
        raise ErroDeNegocio("Email ou senha inválidos", 401, sucesso=False)
    logger.info("Login bem-sucedido: usuario_id=%s", usuario["id"])
    return usuario
