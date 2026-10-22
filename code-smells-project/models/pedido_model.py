"""Acesso a dados de pedidos e itens."""
from collections import defaultdict

PRODUTO_DESCONHECIDO = "Desconhecido"


def criar(conn, usuario_id, status, total):
    cursor = conn.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
        (usuario_id, status, total),
    )
    return cursor.lastrowid


def adicionar_item(conn, pedido_id, produto_id, quantidade, preco_unitario):
    conn.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )


def atualizar_status(conn, pedido_id, status):
    conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))


def listar_pedidos(conn, usuario_id=None):
    """Pedidos com itens e nome do produto em duas consultas (sem N+1)."""
    if usuario_id is None:
        linhas = conn.execute("SELECT id, usuario_id, status, total, criado_em FROM pedidos ORDER BY id").fetchall()
    else:
        linhas = conn.execute(
            "SELECT id, usuario_id, status, total, criado_em FROM pedidos WHERE usuario_id = ? ORDER BY id",
            (usuario_id,),
        ).fetchall()
    pedidos = [dict(linha) for linha in linhas]
    ids = [p["id"] for p in pedidos]
    itens_por_pedido = defaultdict(list)
    if ids:
        marcadores = ",".join("?" * len(ids))  # só "?" gerados; nenhuma entrada do cliente
        itens = conn.execute(
            f"""
            SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, p.nome AS produto_nome
            FROM itens_pedido i LEFT JOIN produtos p ON p.id = i.produto_id
            WHERE i.pedido_id IN ({marcadores})
            ORDER BY i.id
            """,
            ids,
        ).fetchall()
        for item in itens:
            itens_por_pedido[item["pedido_id"]].append({
                "produto_id": item["produto_id"],
                "produto_nome": item["produto_nome"] if item["produto_nome"] is not None else PRODUTO_DESCONHECIDO,
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"],
            })
    for pedido in pedidos:
        pedido["itens"] = itens_por_pedido[pedido["id"]]
    return pedidos


def resumo_vendas(conn):
    """Total de pedidos, soma dos totais e contagem por status."""
    total_pedidos, faturamento = conn.execute("SELECT COUNT(*), SUM(total) FROM pedidos").fetchone()
    por_status = dict(conn.execute("SELECT status, COUNT(*) FROM pedidos GROUP BY status").fetchall())
    return total_pedidos, faturamento, por_status


def contar(conn):
    return conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
