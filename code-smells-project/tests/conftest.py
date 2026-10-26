"""Fixtures compartilhadas.

Cada teste roda num diretório temporário: o banco `loja.db` é criado pelo próprio
app (com o seed) e nunca toca o banco real do projeto. Os módulos do projeto são
descarregados antes de cada teste, então nenhum estado vaza entre testes.

Os testes usam só o cliente HTTP (`app.test_client()`) e o entry point `app.py`,
que expõe o objeto `app`. Não importam módulos internos.
"""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
TOKEN = "token-de-teste"
TOKEN_ERRADO = "token-errado"
FLAGS = ("ENABLE_ADMIN_ROUTES", "ENABLE_SENSITIVE_READS", "ENABLE_WRITE_ROUTES")


def _e_codigo_do_projeto(arquivo):
    caminho = Path(arquivo).resolve()
    return RAIZ in caminho.parents and ".venv" not in caminho.parts and "tests" not in caminho.parts


def _descarregar_projeto():
    for nome, modulo in list(sys.modules.items()):
        if _e_codigo_do_projeto(getattr(modulo, "__file__", None) or ""):
            del sys.modules[nome]


@pytest.fixture
def montar(monkeypatch, tmp_path):
    """Devolve uma função que sobe o app com as flags pedidas.

    flags: nomes de flags T08 a ligar (`ENABLE_*`). As demais ficam desligadas.
    token_enviado: TOKEN, TOKEN_ERRADO ou None (cabeçalho X-Admin-Token ausente).
    """

    def _montar(flags=(), token_enviado=None):
        for chave in (*FLAGS, "ADMIN_TOKEN"):
            monkeypatch.delenv(chave, raising=False)
        for flag in flags:
            monkeypatch.setenv(flag, "true")
        if flags:
            monkeypatch.setenv("ADMIN_TOKEN", TOKEN)
        monkeypatch.chdir(tmp_path)
        monkeypatch.syspath_prepend(str(RAIZ))
        _descarregar_projeto()
        import app as modulo_app

        cliente = modulo_app.app.test_client()
        if token_enviado is not None:
            cliente.environ_base["HTTP_X_ADMIN_TOKEN"] = token_enviado
        return cliente

    return _montar


@pytest.fixture
def cliente(montar):
    """Comportamento original: todas as flags ligadas e o token certo em todas as chamadas."""
    return montar(flags=FLAGS, token_enviado=TOKEN)


@pytest.fixture
def cliente_sem_flags(montar):
    """Flags T08 desligadas (default da aplicação refatorada)."""
    return montar()
