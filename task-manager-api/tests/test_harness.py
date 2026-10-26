from tests.conftest import DB_FILE, PROJECT_ROOT


def test_banco_de_teste_fora_do_projeto(app):
    assert not DB_FILE.startswith(PROJECT_ROOT)


def test_seed_disponivel(admin_client):
    resp = admin_client.get("/tasks")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 10
