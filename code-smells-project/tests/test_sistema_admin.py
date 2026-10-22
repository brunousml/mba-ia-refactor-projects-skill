"""Domínio SISTEMA e ADMIN: caracterização + comportamento novo."""
import json

import pytest

SEGREDO = "minha-chave-super-secreta-123"


def _contagens(query_db):
    return {
        t: query_db(f"SELECT COUNT(*) AS n FROM {t}")[0]["n"]
        for t in ("produtos", "usuarios", "pedidos")
    }


# ---------------- caracterização ----------------

def test_index_contrato(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.get_json() == {
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "1.0.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    }


@pytest.mark.parametrize("rota", ["/", "/health"])
def test_rotas_publicas_sem_flags(make_client, rota):
    assert make_client().get(rota).status_code == 200


def test_health_contrato(client):
    r = client.get("/health")
    assert r.status_code == 200
    corpo = r.get_json()
    assert corpo["status"] == "ok"
    assert corpo["database"] == "connected"
    assert corpo["counts"] == {"produtos": 10, "usuarios": 3, "pedidos": 0}
    assert corpo["versao"] == "1.0.0"
    assert "ambiente" in corpo


def test_reset_db(client, query_db):
    r = client.post("/admin/reset-db")
    assert r.status_code == 200
    assert r.get_json() == {"mensagem": "Banco de dados resetado", "sucesso": True}
    for t in ("produtos", "usuarios", "pedidos", "itens_pedido"):
        assert query_db(f"SELECT COUNT(*) AS n FROM {t}")[0]["n"] == 0


def test_query_select(client):
    r = client.post("/admin/query", json={"sql": "SELECT id FROM produtos ORDER BY id"})
    assert r.status_code == 200
    corpo = r.get_json()
    assert corpo["sucesso"] is True
    assert len(corpo["dados"]) == 10
    assert corpo["dados"][0] == {"id": 1}


def test_query_update_persiste(client, query_db):
    r = client.post("/admin/query", json={"sql": "UPDATE produtos SET estoque = 77 WHERE id = 1"})
    assert r.status_code == 200
    assert r.get_json() == {"mensagem": "Query executada", "sucesso": True}
    assert query_db("SELECT estoque FROM produtos WHERE id = 1")[0]["estoque"] == 77


def test_query_sql_vazio_400(client):
    r = client.post("/admin/query", json={"sql": ""})
    assert r.status_code == 400
    assert "erro" in r.get_json()


def test_query_sql_invalido_500(client):
    r = client.post("/admin/query", json={"sql": "SELECT * FROM tabela_inexistente"})
    assert r.status_code == 500
    assert "erro" in r.get_json()


def test_rota_inexistente_404(client):
    assert client.get("/nao-existe").status_code == 404


# ---------------- comportamento novo ----------------

# comportamento novo
def test_health_nao_expoe_secret_key(client):
    r = client.get("/health")
    corpo = r.get_json()
    assert "secret_key" not in corpo
    assert SEGREDO not in r.get_data(as_text=True)


# comportamento novo
def test_health_debug_false_por_default(client):
    assert client.get("/health").get_json().get("debug", False) is False


# comportamento novo
def test_health_nao_expoe_secret_key_do_ambiente(make_client):
    c = make_client(flags=True, SECRET_KEY="abc-valor-unico-xyz")
    assert "abc-valor-unico-xyz" not in c.get("/health").get_data(as_text=True)


ADMIN = [
    ("/admin/reset-db", None),
    ("/admin/query", {"sql": "DELETE FROM produtos"}),
]


# comportamento novo
@pytest.mark.parametrize("rota,corpo", ADMIN)
def test_admin_sem_flags_403(make_client, query_db, rota, corpo):
    c = make_client()
    antes = _contagens(query_db)
    assert c.post(rota, json=corpo).status_code == 403
    assert _contagens(query_db) == antes


# comportamento novo
@pytest.mark.parametrize("rota,corpo", ADMIN)
def test_admin_sem_token_401(make_client, query_db, rota, corpo):
    c = make_client(flags=True, enviar_token=False)
    antes = _contagens(query_db)
    assert c.post(rota, json=corpo).status_code == 401
    assert _contagens(query_db) == antes


# comportamento novo
@pytest.mark.parametrize("rota,corpo", ADMIN)
def test_admin_token_errado_401(make_client, query_db, rota, corpo):
    c = make_client(flags=True, enviar_token=False)
    antes = _contagens(query_db)
    r = c.post(rota, json=corpo, headers={"X-Admin-Token": "errado"})
    assert r.status_code == 401
    assert _contagens(query_db) == antes


# comportamento novo
def test_query_sem_corpo_json_400(client):
    assert client.post("/admin/query").status_code == 400


# comportamento novo
def test_query_sql_invalido_nao_vaza_erro_interno(client):
    r = client.post("/admin/query", json={"sql": "SELECT * FROM tabela_inexistente"})
    assert r.status_code == 500
    texto = r.get_data(as_text=True)
    assert "no such table" not in texto
    assert "tabela_inexistente" not in texto
    assert "erro" in json.loads(texto)
