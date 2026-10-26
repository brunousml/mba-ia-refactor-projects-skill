from models.database import get_db
from utils.senha import gerar_hash, verificar_senha


def _linha_para_usuario(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "senha": row["senha"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"]
    }


def get_todos_usuarios():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios")
    return [_linha_para_usuario(row) for row in cursor.fetchall()]


def get_usuario_por_id(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (id,))
    row = cursor.fetchone()
    return _linha_para_usuario(row) if row else None


def login_usuario(email, senha):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row and verificar_senha(senha, row["senha"]):
        return {
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "tipo": row["tipo"]
        }
    return None


def criar_usuario(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, gerar_hash(senha), tipo)
    )
    db.commit()
    return cursor.lastrowid
