"""Constantes de regra de negócio, com nome (T12)."""

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
STATUS_PEDIDO_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]

NOME_PRODUTO_MINIMO = 2
NOME_PRODUTO_MAXIMO = 200

# (faturamento acima de, taxa de desconto). A primeira faixa que casar vale.
FAIXAS_DESCONTO = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]
