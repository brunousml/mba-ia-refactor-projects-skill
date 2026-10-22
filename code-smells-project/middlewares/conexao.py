"""T07: uma conexão por requisição, com commit no sucesso e rollback no erro."""
from flask import g


def conexao_atual():
    return g.conn


def desfazer_requisicao():
    conn = g.pop("conn", None)
    if conn is not None:
        conn.rollback()
        conn.close()


def registrar_conexao(app, banco):
    @app.before_request
    def abrir_conexao():
        g.conn = banco.abrir()

    @app.teardown_request
    def fechar_conexao(erro=None):
        conn = g.pop("conn", None)
        if conn is None:
            return
        if erro is None:
            conn.commit()
        else:
            conn.rollback()
        conn.close()
