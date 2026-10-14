from flask import current_app, g


def registrar(app, banco):
    app.extensions["banco"] = banco

    @app.teardown_appcontext
    def fechar_conexao(_erro=None):
        conn = g.pop("conn", None)
        if conn is not None:
            conn.close()   # o que não foi confirmado pelo serviço é descartado


def conexao_da_requisicao():
    if "conn" not in g:
        g.conn = current_app.extensions["banco"].abrir()
    return g.conn
