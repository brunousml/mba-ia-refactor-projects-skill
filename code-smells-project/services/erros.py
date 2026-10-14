class ErroDeNegocio(Exception):
    """Erro de domínio com status sugerido. `sucesso` só entra no corpo quando a rota original o devolvia."""

    def __init__(self, mensagem, status=400, sucesso=None):
        super().__init__(mensagem)
        self.status = status
        self.sucesso = sucesso
