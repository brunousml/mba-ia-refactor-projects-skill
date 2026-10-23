from models.database import get_db


def inserir_pedido(usuario_id, total):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total)
    )
    return cursor.lastrowid


def inserir_item(pedido_id, produto_id, quantidade, preco_unitario):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario)
    )


def _montar_pedidos(db, pedidos_rows):
    """Carrega os itens de todos os pedidos em uma consulta (T09), sem uma consulta por pedido."""
    pedidos = []
    por_id = {}
    for row in pedidos_rows:
        pedido = {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": []
        }
        pedidos.append(pedido)
        por_id[row["id"]] = pedido

    if por_id:
        marcadores = ",".join("?" * len(por_id))  # só "?" gerados; nenhum valor do cliente
        itens = db.execute(
            "SELECT ip.pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario, p.nome AS produto_nome "
            "FROM itens_pedido ip LEFT JOIN produtos p ON p.id = ip.produto_id "
            "WHERE ip.pedido_id IN (" + marcadores + ") ORDER BY ip.id",
            list(por_id)
        ).fetchall()
        for item in itens:
            por_id[item["pedido_id"]]["itens"].append({
                "produto_id": item["produto_id"],
                "produto_nome": item["produto_nome"] if item["produto_nome"] is not None else "Desconhecido",
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"]
            })
    return pedidos


def get_pedidos_usuario(usuario_id):
    db = get_db()
    rows = db.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,)).fetchall()
    return _montar_pedidos(db, rows)


def get_todos_pedidos():
    db = get_db()
    rows = db.execute("SELECT * FROM pedidos").fetchall()
    return _montar_pedidos(db, rows)


def resumo_vendas():
    """Contagens e soma brutas. As regras de desconto ficam no serviço de relatório (T06)."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total) FROM pedidos")
    faturamento = cursor.fetchone()[0]
    if faturamento is None:
        faturamento = 0

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
    pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'")
    aprovados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'")
    cancelados = cursor.fetchone()[0]

    return {
        "total_pedidos": total_pedidos,
        "faturamento": faturamento,
        "pendentes": pendentes,
        "aprovados": aprovados,
        "cancelados": cancelados,
    }


def atualizar_status_pedido(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()
    return True
