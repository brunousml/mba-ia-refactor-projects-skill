"""Usuários e login: caracterização + comportamento novo (T04, T05, T08, SQLi)."""
import pytest

SEED = [
    (1, "admin@loja.com", "admin123"),
    (2, "joao@email.com", "123456"),
    (3, "maria@email.com", "senha123"),
]


# ---------- caracterização ----------

def test_listar_usuarios(client):
    r = client.get("/usuarios")
    assert r.status_code == 200
    dados = r.get_json()["dados"]
    assert len(dados) == 3
    for u in dados:
        assert {"id", "nome", "email", "tipo", "criado_em"} <= set(u)


def test_buscar_usuario(client):
    r = client.get("/usuarios/2")
    assert r.status_code == 200
    u = r.get_json()["dados"]
    assert u["id"] == 2 and u["nome"] == "João Silva" and u["email"] == "joao@email.com"


def test_buscar_usuario_inexistente(client):
    assert client.get("/usuarios/999").status_code == 404


def test_criar_usuario(client):
    r = client.post("/usuarios", json={"nome": "Ana", "email": "ana@x.com", "senha": "abc"})
    assert r.status_code == 201
    assert isinstance(r.get_json()["dados"]["id"], int)


def test_criar_usuario_sem_campos(client):
    assert client.post("/usuarios", json={"nome": "Ana"}).status_code == 400


@pytest.mark.parametrize("uid,email,senha", SEED)
def test_login_seed(client, uid, email, senha):
    r = client.post("/login", json={"email": email, "senha": senha})
    assert r.status_code == 200
    corpo = r.get_json()
    assert corpo["mensagem"] == "Login OK"
    assert {"id", "nome", "email", "tipo"} <= set(corpo["dados"])
    assert corpo["dados"]["id"] == uid


def test_login_usuario_recem_criado(client):
    client.post("/usuarios", json={"nome": "Ana", "email": "ana@x.com", "senha": "abc"})
    r = client.post("/login", json={"email": "ana@x.com", "senha": "abc"})
    assert r.status_code == 200
    assert r.get_json()["dados"]["email"] == "ana@x.com"


def test_login_senha_errada(client):
    assert client.post("/login", json={"email": "admin@loja.com", "senha": "x"}).status_code == 401


def test_login_campos_vazios(client):
    assert client.post("/login", json={"email": "", "senha": ""}).status_code == 400


def test_login_publico_sem_flags(make_client):
    c = make_client()
    assert c.post("/login", json={"email": "admin@loja.com", "senha": "admin123"}).status_code == 200


# ---------- comportamento novo ----------

def test_listar_sem_senha(client):
    # comportamento novo
    for u in client.get("/usuarios").get_json()["dados"]:
        assert "senha" not in u


def test_buscar_sem_senha(client):
    # comportamento novo
    assert "senha" not in client.get("/usuarios/1").get_json()["dados"]


def test_senha_seed_nao_em_texto_puro(client, query_db):
    # comportamento novo
    client.get("/usuarios")  # o banco nasce na primeira requisição
    linhas = {r["id"]: r["senha"] for r in query_db("SELECT id, senha FROM usuarios")}
    for uid, _, senha in SEED:
        assert linhas[uid] != senha


def test_senha_criada_nao_em_texto_puro(client, query_db):
    # comportamento novo
    uid = client.post("/usuarios", json={"nome": "Ana", "email": "ana@x.com", "senha": "abc"}).get_json()["dados"]["id"]
    assert query_db("SELECT senha FROM usuarios WHERE id = ?", (uid,))[0]["senha"] != "abc"


@pytest.mark.parametrize("rota", ["/usuarios", "/usuarios/1"])
def test_leitura_sem_flag_403(make_client, rota):
    # comportamento novo
    assert make_client().get(rota).status_code == 403


@pytest.mark.parametrize("rota", ["/usuarios", "/usuarios/1"])
def test_leitura_sem_token_401(make_client, rota):
    # comportamento novo
    assert make_client(flags=True, enviar_token=False).get(rota).status_code == 401


def test_criar_sem_flag_403(make_client):
    # comportamento novo
    r = make_client().post("/usuarios", json={"nome": "A", "email": "a@x.com", "senha": "1"})
    assert r.status_code == 403


def test_criar_sem_token_401(make_client):
    # comportamento novo
    r = make_client(flags=True, enviar_token=False).post(
        "/usuarios", json={"nome": "A", "email": "a@x.com", "senha": "1"})
    assert r.status_code == 401


def test_login_injecao_sql(client):
    # comportamento novo
    r = client.post("/login", json={"email": "' OR '1'='1' --", "senha": "x"})
    assert r.status_code == 401


def test_login_sem_corpo(client):
    # comportamento novo
    r = client.post("/login", data="", content_type="application/json")
    assert r.status_code == 400


def test_login_email_nao_string(client):
    # comportamento novo
    assert client.post("/login", json={"email": 123, "senha": "x"}).status_code == 400


def test_criar_nome_com_aspas(client):
    # comportamento novo
    r = client.post("/usuarios", json={"nome": "D'Ávila", "email": "d@x.com", "senha": "abc"})
    assert r.status_code == 201
