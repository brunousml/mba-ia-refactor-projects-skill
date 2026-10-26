import sqlite3

from flask import g

from config import settings
from utils.senha import gerar_hash


def abrir_conexao():
    conexao = sqlite3.connect(settings.DB_PATH)
    conexao.row_factory = sqlite3.Row
    return conexao


def get_db():
    """Uma conexão por requisição (T07). Quem chama precisa estar dentro do contexto da aplicação."""
    if "db" not in g:
        g.db = abrir_conexao()
    return g.db


def desfazer_transacao():
    """Desfaz a escrita pendente da requisição. O handler de 500 chama isto, porque, quando ele trata
    a exceção, o teardown recebe erro=None e faria commit da escrita parcial."""
    db = g.get("db")
    if db is not None:
        db.rollback()


def fechar_db(erro=None):
    """Fim da requisição: confirma se deu certo, desfaz se deu erro, e fecha."""
    db = g.pop("db", None)
    if db is None:
        return
    if erro is None:
        db.commit()
    else:
        db.rollback()
    db.close()


def inicializar_banco():
    """Cria as tabelas e o seed na subida, antes de qualquer requisição."""
    db = abrir_conexao()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            descricao TEXT,
            preco REAL,
            estoque INTEGER,
            categoria TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT,
            senha TEXT,
            tipo TEXT DEFAULT 'cliente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            status TEXT DEFAULT 'pendente',
            total REAL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER,
            preco_unitario REAL
        )
    """)
    db.commit()

    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone()[0] == 0:
        produtos = [
            ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
            ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
            ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
            ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
            ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
            ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
            ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
            ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
            ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
            ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
        ]
        cursor.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            produtos
        )

        # Usuários de exemplo só fora de produção (AP-01). As senhas de exemplo são as mesmas de antes,
        # gravadas como hash (T04).
        if settings.APP_ENV != "production":
            usuarios = [
                ("Admin", "admin@loja.com", gerar_hash("admin123"), "admin"),
                ("João Silva", "joao@email.com", gerar_hash("123456"), "cliente"),
                ("Maria Santos", "maria@email.com", gerar_hash("senha123"), "cliente"),
            ]
            cursor.executemany(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                usuarios
            )
        db.commit()
    db.close()
