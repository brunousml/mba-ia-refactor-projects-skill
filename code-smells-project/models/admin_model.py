"""Operações administrativas sobre o banco (expostas só atrás do guard de admin)."""

TABELAS_NA_ORDEM_DE_LIMPEZA = ["itens_pedido", "pedidos", "produtos", "usuarios"]


def limpar_tabelas(conn):
    for tabela in TABELAS_NA_ORDEM_DE_LIMPEZA:
        conn.execute(f"DELETE FROM {tabela}")  # nome vem da lista fixa acima


def executar_sql(conn, sql):
    """Executa o SQL recebido. Devolve as linhas se for SELECT, senão None."""
    cursor = conn.execute(sql)
    if sql.strip().upper().startswith("SELECT"):
        return [dict(linha) for linha in cursor.fetchall()]
    return None
