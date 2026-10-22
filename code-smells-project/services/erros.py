"""Erro de domínio: o serviço lança, o middleware de erro traduz para a resposta."""


class ErroDeNegocio(Exception):
    def __init__(self, mensagem, status=400, com_sucesso=False):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status
        self.com_sucesso = com_sucesso  # algumas respostas originais trazem "sucesso": false

    def corpo(self):
        corpo = {"erro": self.mensagem}
        if self.com_sucesso:
            corpo["sucesso"] = False
        return corpo
