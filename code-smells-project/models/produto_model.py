def listar(conn):
    return [dict(row) for row in conn.execute("SELECT * FROM produtos")]


def buscar_por_id(conn, produto_id):
    row = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return dict(row) if row else None


def criar(conn, nome, descricao, preco, estoque, categoria):
    cursor = conn.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    return cursor.lastrowid


def atualizar(conn, produto_id, nome, descricao, preco, estoque, categoria):
    conn.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )


def deletar(conn, produto_id):
    conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))


def buscar(conn, termo, categoria=None, preco_min=None, preco_max=None):
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max:
        query += " AND preco <= ?"
        params.append(preco_max)
    return [dict(row) for row in conn.execute(query, params)]


def contar(conn):
    return conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
