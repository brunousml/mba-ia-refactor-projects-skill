class ErroDominio(Exception):
    """Erro de regra de negócio. O middleware de erro traduz para a resposta (T10).

    `corpo_extra` acrescenta chaves ao corpo JSON, para manter o contrato de cada rota.
    """

    def __init__(self, mensagem, status=400, corpo_extra=None):
        super().__init__(mensagem)
        self.status = status
        self.corpo_extra = corpo_extra or {}
