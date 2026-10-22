"""Fixtures comuns.

Cada teste importa a aplicação do zero, com o diretório de trabalho num
diretório temporário (o banco `loja.db` nasce ali, já com o seed). Funciona
com o entry point original (`app.app`) e com a fábrica (`app.create_app()`).
"""
import importlib
import sqlite3
import sys
from pathlib import Path

import pytest

PROJETO = Path(__file__).resolve().parents[1]
if str(PROJETO) not in sys.path:
    sys.path.insert(0, str(PROJETO))

MODULOS_DO_PROJETO = (
    "app", "controllers", "models", "database", "config", "services",
    "routes", "middlewares", "serializers", "utils",
)
FLAGS = ("ENABLE_ADMIN_ROUTES", "ENABLE_SENSITIVE_READS", "ENABLE_WRITE_ROUTES")
TOKEN = "token-de-teste"


def _descarregar_modulos():
    for nome in list(sys.modules):
        if nome.split(".")[0] in MODULOS_DO_PROJETO:
            del sys.modules[nome]


@pytest.fixture
def make_client(tmp_path, monkeypatch):
    """Cria um cliente de teste. `flags=True` liga as três flags do T08 e
    envia `X-Admin-Token` válido em toda requisição (comportamento original)."""

    def _criar(flags=False, token=TOKEN, enviar_token=True, **env):
        monkeypatch.chdir(tmp_path)
        for nome in FLAGS + ("ADMIN_TOKEN", "DB_PATH", "SECRET_KEY", "DEBUG", "APP_ENV"):
            monkeypatch.delenv(nome, raising=False)
        if flags:
            for nome in FLAGS:
                monkeypatch.setenv(nome, "true")
        if token:
            monkeypatch.setenv("ADMIN_TOKEN", token)
        for nome, valor in env.items():
            monkeypatch.setenv(nome, valor)
        _descarregar_modulos()
        modulo = importlib.import_module("app")
        aplicacao = modulo.create_app() if hasattr(modulo, "create_app") else modulo.app
        aplicacao.config["TESTING"] = True
        cliente = aplicacao.test_client()
        if flags and enviar_token and token:
            cliente.environ_base["HTTP_X_ADMIN_TOKEN"] = token
        return cliente

    yield _criar
    _descarregar_modulos()


@pytest.fixture
def client(make_client):
    """Cliente com as flags ligadas e o token: reproduz o contrato original."""
    return make_client(flags=True)


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "loja.db"


@pytest.fixture
def query_db(db_path):
    """Lê o banco do teste direto pelo arquivo (só leitura de verificação)."""

    def _consultar(sql, params=()):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]
        finally:
            conn.close()

    return _consultar
