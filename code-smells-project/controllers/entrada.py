"""Leitura da requisição na borda (T17)."""
from flask import request

from services.erros import ErroDeNegocio


def corpo_json():
    """Corpo JSON como dict, ou None se ausente ou malformado."""
    dados = request.get_json(silent=True)
    return dados if isinstance(dados, dict) else None


def numero_da_query(nome):
    valor = request.args.get(nome, None)
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError:
        raise ErroDeNegocio(f"{nome} deve ser numérico")
