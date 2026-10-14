CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = [STATUS_PENDENTE, STATUS_APROVADO, "enviado", "entregue", STATUS_CANCELADO]

# (faturamento acima de, taxa de desconto), da maior faixa para a menor
FAIXAS_DE_DESCONTO = [(10000, 0.1), (5000, 0.05), (1000, 0.02)]

TIPO_USUARIO_PADRAO = "cliente"
VERSAO_API = "1.0.0"
