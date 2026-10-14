import logging

from models import admin_model

logger = logging.getLogger(__name__)


def resetar_banco(conn):
    admin_model.resetar_banco(conn)
    conn.commit()
    logger.warning("Banco de dados resetado pela rota de administração")


def executar_sql(conn, query):
    linhas = admin_model.executar_sql(conn, query)
    if linhas is None:
        conn.commit()
    return linhas
