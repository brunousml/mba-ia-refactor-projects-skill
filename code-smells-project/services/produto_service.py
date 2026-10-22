"""Regras de produto: validação única para criar e atualizar (T16)."""
import logging

from config.regras import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_PRODUTO_MAX, NOME_PRODUTO_MIN
from models import produto_model
from serializers.produto_serializer import produto_publico
from services.erros import ErroDeNegocio
from utils.tipos import eh_inteiro, eh_numero

logger = logging.getLogger(__name__)


def validar_dados_produto(dados):
    """Devolve (nome, descricao, preco, estoque, categoria) ou lança ErroDeNegocio."""
    if not dados:
        raise ErroDeNegocio("Dados inválidos")
    if "nome" not in dados:
        raise ErroDeNegocio("Nome é obrigatório")
    if "preco" not in dados:
        raise ErroDeNegocio("Preço é obrigatório")
    if "estoque" not in dados:
        raise ErroDeNegocio("Estoque é obrigatório")

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
        raise ErroDeNegocio("Estoque deve ser inteiro")
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
    return nome, descricao, preco, estoque, categoria


def listar(conn):
    return [produto_publico(p) for p in produto_model.listar(conn)]


def buscar(conn, produto_id):
    produto = produto_model.buscar_por_id(conn, produto_id)
    if produto is None:
        raise ErroDeNegocio("Produto não encontrado", 404, com_sucesso=True)
    return produto_publico(produto)


def pesquisar(conn, termo, categoria, preco_min, preco_max):
    return [produto_publico(p) for p in produto_model.pesquisar(conn, termo, categoria, preco_min, preco_max)]


def criar(conn, dados):
    campos = validar_dados_produto(dados)
    produto_id = produto_model.criar(conn, *campos)
    logger.info("Produto criado: id=%s", produto_id)
    return produto_id


def atualizar(conn, produto_id, dados):
    if produto_model.buscar_por_id(conn, produto_id) is None:
        raise ErroDeNegocio("Produto não encontrado", 404)
    campos = validar_dados_produto(dados)
    produto_model.atualizar(conn, produto_id, *campos)


def deletar(conn, produto_id):
    if produto_model.buscar_por_id(conn, produto_id) is None:
        raise ErroDeNegocio("Produto não encontrado", 404)
    produto_model.deletar(conn, produto_id)
    logger.info("Produto deletado: id=%s", produto_id)
