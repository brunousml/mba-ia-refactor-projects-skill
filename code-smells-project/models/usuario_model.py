def listar(conn):
    return [dict(row) for row in conn.execute("SELECT * FROM usuarios")]


def buscar_por_id(conn, usuario_id):
    row = conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return dict(row) if row else None


def buscar_por_email(conn, email):
    row = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def criar(conn, nome, email, senha_hash, tipo="cliente"):
    cursor = conn.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    return cursor.lastrowid


def contar(conn):
    return conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
