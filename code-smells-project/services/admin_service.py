"""Operações administrativas (rotas atrás do guard de admin)."""
import logging

from models import admin_model

logger = logging.getLogger(__name__)


def resetar_banco(conn):
    admin_model.limpar_tabelas(conn)
    logger.warning("Banco de dados resetado via /admin/reset-db")


def executar_sql(conn, sql):
    logger.warning("SQL administrativo executado via /admin/query")
    return admin_model.executar_sql(conn, sql)
