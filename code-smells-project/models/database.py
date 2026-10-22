"""Banco SQLite: abertura de conexões, schema e seed."""
import logging
import sqlite3

from utils.senha import eh_hash, gerar_hash

logger = logging.getLogger(__name__)

SCHEMA = [
    """
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
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
]

PRODUTOS_SEED = [
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

# Senhas de exemplo do seed original; gravadas só como hash.
USUARIOS_SEED = [
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
]


class Banco:
    def __init__(self, caminho):
        self._caminho = caminho

    def abrir(self):
        conn = sqlite3.connect(self._caminho)
        conn.row_factory = sqlite3.Row
        return conn

    def inicializar(self):
        conn = self.abrir()
        try:
            for ddl in SCHEMA:
                conn.execute(ddl)
            if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
                conn.executemany(
                    "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                    PRODUTOS_SEED,
                )
                conn.executemany(
                    "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                    [(nome, email, gerar_hash(senha), tipo) for nome, email, senha, tipo in USUARIOS_SEED],
                )
            self._migrar_senhas_em_texto(conn)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _migrar_senhas_em_texto(conn):
        """Bancos criados pela versão antiga guardam senha em texto puro."""
        for linha in conn.execute("SELECT id, senha FROM usuarios").fetchall():
            if linha["senha"] is not None and not eh_hash(linha["senha"]):
                conn.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (gerar_hash(linha["senha"]), linha["id"]))
                logger.info("Senha migrada para hash: usuario_id=%s", linha["id"])
