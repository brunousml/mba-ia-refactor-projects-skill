def resetar_banco(conn):
    for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):
        conn.execute(f"DELETE FROM {tabela}")   # seguro: nomes vêm da tupla fixa


def executar_sql(conn, query):
    """SQL livre de administração: só alcançável atrás do guard de admin (flag + token)."""
    cursor = conn.execute(query)
    if query.strip().upper().startswith("SELECT"):
        return [dict(row) for row in cursor.fetchall()]
    return None
