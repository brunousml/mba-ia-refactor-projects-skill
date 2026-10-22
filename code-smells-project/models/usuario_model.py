"""Acesso a dados de usuários."""

COLUNAS = "id, nome, email, senha, tipo, criado_em"


def listar(conn):
    return conn.execute(f"SELECT {COLUNAS} FROM usuarios").fetchall()


def buscar_por_id(conn, usuario_id):
    return conn.execute(f"SELECT {COLUNAS} FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()


def buscar_por_email(conn, email):
    return conn.execute(f"SELECT {COLUNAS} FROM usuarios WHERE email = ? ORDER BY id", (email,)).fetchone()


def criar(conn, nome, email, senha_hash, tipo):
    cursor = conn.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    return cursor.lastrowid


def contar(conn):
    return conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
