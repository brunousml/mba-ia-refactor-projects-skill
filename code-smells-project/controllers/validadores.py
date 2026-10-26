"""Validação de formato na borda (T17) e regra compartilhada de cadastro de produto (T16).

Cada função devolve a mensagem de erro (400) ou None. Quem chama decide a resposta.
"""
from flask import request

from config.regras import CATEGORIAS_VALIDAS, NOME_PRODUTO_MAXIMO, NOME_PRODUTO_MINIMO, STATUS_PEDIDO_VALIDOS
from services.erros import ErroDominio


def corpo_json():
    """Corpo JSON ou None. Corpo ausente ou malformado vira None, nunca exceção (T17)."""
    return request.get_json(silent=True)


def _numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def validar_produto(dados):
    if not dados:
        return "Dados inválidos"
    if "nome" not in dados:
        return "Nome é obrigatório"
    if "preco" not in dados:
        return "Preço é obrigatório"
    if "estoque" not in dados:
        return "Estoque é obrigatório"

    nome, preco, estoque = dados["nome"], dados["preco"], dados["estoque"]
    if not isinstance(nome, str):
        return "Nome deve ser texto"
    if not _numero(preco):
        return "Preço deve ser numérico"
    if not _inteiro(estoque):
        return "Estoque deve ser inteiro"
    if preco < 0:
        return "Preço não pode ser negativo"
    if estoque < 0:
        return "Estoque não pode ser negativo"
    if len(nome) < NOME_PRODUTO_MINIMO:
        return "Nome muito curto"
    if len(nome) > NOME_PRODUTO_MAXIMO:
        return "Nome muito longo"
    if dados.get("categoria", "geral") not in CATEGORIAS_VALIDAS:
        return "Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS)
    return None


def validar_usuario(dados):
    if not dados:
        return "Dados inválidos"
    if not dados.get("nome") or not dados.get("email") or not dados.get("senha"):
        return "Nome, email e senha são obrigatórios"
    return None


def validar_login(dados):
    if not isinstance(dados, dict):
        return "Dados inválidos"
    if not dados.get("email") or not dados.get("senha"):
        return "Email e senha são obrigatórios"
    return None


def validar_pedido(dados):
    if not dados:
        return "Dados inválidos"
    usuario_id = dados.get("usuario_id")
    if not usuario_id:
        return "Usuario ID é obrigatório"
    if not _inteiro(usuario_id):
        return "Usuario ID deve ser inteiro"
    itens = dados.get("itens", [])
    if not itens:
        return "Pedido deve ter pelo menos 1 item"
    if not isinstance(itens, list):
        return "Itens devem ser uma lista"
    for item in itens:
        if not isinstance(item, dict) or not _inteiro(item.get("produto_id")):
            return "Produto do item deve ser inteiro"
        quantidade = item.get("quantidade")
        if not _inteiro(quantidade) or quantidade <= 0:
            return "Quantidade deve ser inteiro maior que zero"
    return None


def validar_status(dados):
    if not isinstance(dados, dict):
        return "Dados inválidos"
    if dados.get("status", "") not in STATUS_PEDIDO_VALIDOS:
        return "Status inválido"
    return None


def converter_preco(valor, nome):
    """Converte o filtro de preço da query string. Valor inválido vira 400 (T17)."""
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError:
        raise ErroDominio(nome + " deve ser numérico", 400)
