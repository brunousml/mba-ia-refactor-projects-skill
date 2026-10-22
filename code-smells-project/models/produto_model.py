"""Acesso a dados de produtos."""

COLUNAS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"


def listar(conn):
    return conn.execute(f"SELECT {COLUNAS} FROM produtos").fetchall()


def buscar_por_id(conn, produto_id):
    return conn.execute(f"SELECT {COLUNAS} FROM produtos WHERE id = ?", (produto_id,)).fetchone()


def buscar_por_ids(conn, ids):
    if not ids:
        return {}
    marcadores = ",".join("?" * len(ids))  # só "?" gerados; nenhuma entrada do cliente
    linhas = conn.execute(f"SELECT {COLUNAS} FROM produtos WHERE id IN ({marcadores})", list(ids)).fetchall()
    return {linha["id"]: linha for linha in linhas}


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


def baixar_estoque(conn, produto_id, quantidade):
    conn.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (quantidade, produto_id))


def pesquisar(conn, termo=None, categoria=None, preco_min=None, preco_max=None):
    condicoes, params = [], []
    if termo:
        condicoes.append("(nome LIKE ? OR descricao LIKE ?)")
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        condicoes.append("categoria = ?")
        params.append(categoria)
    if preco_min:
        condicoes.append("preco >= ?")
        params.append(preco_min)
    if preco_max:
        condicoes.append("preco <= ?")
        params.append(preco_max)
    sql = f"SELECT {COLUNAS} FROM produtos WHERE 1=1"
    for condicao in condicoes:
        sql += " AND " + condicao  # condições fixas do código; valores vão em params
    return conn.execute(sql, params).fetchall()


def contar(conn):
    return conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
