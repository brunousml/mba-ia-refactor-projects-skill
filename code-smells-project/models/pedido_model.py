from collections import defaultdict

from config.regras import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE


def _marcadores(valores):
    return ",".join("?" * len(valores))   # só "?" gerados; nenhuma entrada do cliente


def buscar_produtos(conn, produto_ids):
    """Produtos por id numa consulta só: {id: row}."""
    ids = list(set(produto_ids))
    rows = conn.execute(f"SELECT * FROM produtos WHERE id IN ({_marcadores(ids)})", ids).fetchall()
    return {row["id"]: row for row in rows}


def inserir_pedido(conn, usuario_id, total):
    cursor = conn.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
        (usuario_id, STATUS_PENDENTE, total),
    )
    return cursor.lastrowid


def inserir_item_e_baixar_estoque(conn, pedido_id, produto_id, quantidade, preco_unitario):
    conn.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )
    conn.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (quantidade, produto_id))


def _com_itens(conn, rows):
    pedidos = [dict(row) for row in rows]
    ids = [pedido["id"] for pedido in pedidos]
    itens_por_pedido = defaultdict(list)
    if ids:
        itens = conn.execute(
            f"""
            SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario,
                   COALESCE(p.nome, 'Desconhecido') AS produto_nome
            FROM itens_pedido i
            LEFT JOIN produtos p ON p.id = i.produto_id
            WHERE i.pedido_id IN ({_marcadores(ids)})
            ORDER BY i.id
            """,
            ids,
        )
        for item in itens:
            itens_por_pedido[item["pedido_id"]].append(dict(item))
    for pedido in pedidos:
        pedido["itens"] = itens_por_pedido[pedido["id"]]
    return pedidos


def listar_por_usuario(conn, usuario_id):
    rows = conn.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,)).fetchall()
    return _com_itens(conn, rows)


def listar_todos(conn):
    return _com_itens(conn, conn.execute("SELECT * FROM pedidos").fetchall())


def existe(conn, pedido_id):
    return conn.execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone() is not None


def atualizar_status(conn, pedido_id, novo_status):
    conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))


def contar(conn):
    return conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]


def totais_de_vendas(conn):
    row = conn.execute(
        """
        SELECT COUNT(*) AS total_pedidos,
               SUM(total) AS faturamento,
               COALESCE(SUM(status = ?), 0) AS pendentes,
               COALESCE(SUM(status = ?), 0) AS aprovados,
               COALESCE(SUM(status = ?), 0) AS cancelados
        FROM pedidos
        """,
        (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
    ).fetchone()
    return dict(row)
