from models.database import get_db


def resetar():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")
    db.commit()


def executar(query):
    """Executa SQL bruto (rota de administração). Devolve as linhas em SELECT; None nos demais casos."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(query)
    if query.strip().upper().startswith("SELECT"):
        return [dict(row) for row in cursor.fetchall()]
    db.commit()
    return None
