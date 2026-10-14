import logging

from config.regras import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_PRODUTO_MAX, NOME_PRODUTO_MIN
from models import produto_model
from services.erros import ErroDeNegocio
from utils.tipos import eh_inteiro, eh_numero

logger = logging.getLogger(__name__)

CAMPOS_OBRIGATORIOS = (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque"))


def validar_produto(dados):
    """Regra única de produto, usada na criação e na atualização."""
    for campo, rotulo in CAMPOS_OBRIGATORIOS:
        if campo not in dados:
            raise ErroDeNegocio(f"{rotulo} é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ErroDeNegocio("Nome deve ser texto")
    if not isinstance(descricao, str):
        raise ErroDeNegocio("Descrição deve ser texto")
    if not eh_numero(preco):
        raise ErroDeNegocio("Preço deve ser numérico")
    if not eh_inteiro(estoque):
        raise ErroDeNegocio("Estoque deve ser um número inteiro")
    if preco < 0:
        raise ErroDeNegocio("Preço não pode ser negativo")
    if estoque < 0:
        raise ErroDeNegocio("Estoque não pode ser negativo")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ErroDeNegocio("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ErroDeNegocio("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ErroDeNegocio("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def listar(conn):
    return produto_model.listar(conn)


def obter(conn, produto_id, sucesso_no_erro=None):
    produto = produto_model.buscar_por_id(conn, produto_id)
    if produto is None:
        raise ErroDeNegocio("Produto não encontrado", 404, sucesso=sucesso_no_erro)
    return produto


def buscar(conn, termo, categoria, preco_min, preco_max):
    return produto_model.buscar(conn, termo, categoria, preco_min, preco_max)


def criar(conn, dados):
    produto = validar_produto(dados)
    produto_id = produto_model.criar(conn, **produto)
    conn.commit()
    logger.info("Produto criado: produto_id=%s", produto_id)
    return produto_id


def atualizar(conn, produto_id, dados):
    obter(conn, produto_id)
    if not dados:
        raise ErroDeNegocio("Dados inválidos")
    produto_model.atualizar(conn, produto_id, **validar_produto(dados))
    conn.commit()


def deletar(conn, produto_id):
    obter(conn, produto_id)
    produto_model.deletar(conn, produto_id)
    conn.commit()
    logger.info("Produto deletado: produto_id=%s", produto_id)
