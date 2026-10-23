"""Harness comum dos testes.

Isolamento: o banco de cada teste é uma cópia de um banco semeado uma vez numa
pasta temporária. O banco real do projeto (instance/tasks.db) nunca é tocado.

Flags do T08: ficam em app.config (ENABLE_ADMIN_ROUTES, ENABLE_SENSITIVE_READS,
ENABLE_WRITE_ROUTES, ADMIN_TOKEN). `client` deixa tudo desligado; `admin_client`
liga as três e manda o X-Admin-Token. No código original elas não têm efeito.
"""
import os
import shutil
import sys
import tempfile

import flask
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

_TMP = tempfile.mkdtemp(prefix="tm-tests-")
_INSTANCE = os.path.join(_TMP, "instance")
os.makedirs(_INSTANCE, exist_ok=True)
DB_FILE = os.path.join(_INSTANCE, "tasks.db")
SEED_FILE = os.path.join(_TMP, "tasks.db.seed")

ADMIN_TOKEN = "test-admin-token"
FLAGS = ("ENABLE_ADMIN_ROUTES", "ENABLE_SENSITIVE_READS", "ENABLE_WRITE_ROUTES")

# O original usa 'sqlite:///tasks.db', relativo ao instance_path do Flask.
# Apontamos o instance_path para a pasta temporária antes de importar o app.
flask.Flask.auto_find_instance_path = lambda self: _INSTANCE
os.environ["DATABASE_URL"] = "sqlite:///" + DB_FILE
os.environ.setdefault("APP_ENV", "test")
for _flag in FLAGS:
    os.environ.pop(_flag, None)
os.environ.pop("ADMIN_TOKEN", None)

from app import app as flask_app  # noqa: E402
from database import db  # noqa: E402
import seed as seed_module  # noqa: E402


def _seed_once():
    seed_module.seed_data()
    with flask_app.app_context():
        db.session.remove()
        db.engine.dispose()
    shutil.copyfile(DB_FILE, SEED_FILE)


_seed_once()


def _reset_db():
    with flask_app.app_context():
        db.session.remove()
        db.engine.dispose()
    shutil.copyfile(SEED_FILE, DB_FILE)


@pytest.fixture
def app():
    _reset_db()
    flask_app.config["TESTING"] = True
    saved = {k: flask_app.config.get(k) for k in FLAGS + ("ADMIN_TOKEN",)}
    for k in FLAGS:
        flask_app.config[k] = False
    flask_app.config["ADMIN_TOKEN"] = ADMIN_TOKEN
    yield flask_app
    for k, v in saved.items():
        flask_app.config[k] = v
    _reset_db()


@pytest.fixture
def client(app):
    """Flags do T08 desligadas, sem token."""
    return app.test_client()


@pytest.fixture
def flags_on(app):
    """Liga as três flags do T08 (sem mandar token)."""
    for k in FLAGS:
        app.config[k] = True
    return app


@pytest.fixture
def flags_client(flags_on):
    """Flags ligadas, sem token (espera 401 nas rotas guardadas)."""
    return flags_on.test_client()


class _TokenClient:
    def __init__(self, inner, token):
        self._inner = inner
        self._token = token

    def open(self, *args, **kwargs):
        headers = dict(kwargs.pop("headers", None) or {})
        headers.setdefault("X-Admin-Token", self._token)
        kwargs["headers"] = headers
        return self._inner.open(*args, **kwargs)

    def get(self, *a, **k):
        return self.open(*a, method="GET", **k)

    def post(self, *a, **k):
        return self.open(*a, method="POST", **k)

    def put(self, *a, **k):
        return self.open(*a, method="PUT", **k)

    def delete(self, *a, **k):
        return self.open(*a, method="DELETE", **k)


@pytest.fixture
def admin_client(flags_on):
    """Flags ligadas + X-Admin-Token correto: comportamento original."""
    return _TokenClient(flags_on.test_client(), ADMIN_TOKEN)


@pytest.fixture
def wrong_token_client(flags_on):
    """Flags ligadas + token errado (espera 401)."""
    return _TokenClient(flags_on.test_client(), "token-errado")


@pytest.fixture
def db_session(app):
    """Contexto de app com acesso direto ao banco de teste (para asserts)."""
    with app.app_context():
        yield db.session
