"""Testes do domínio PRODUTOS: caracterização do contrato original + comportamento novo."""
import pytest

NOVO = {"nome": "Livro Python", "descricao": "Livro de programação", "preco": 120.5,
        "estoque": 7, "categoria": "livros"}


# ---------------------------------------------------------------- caracterização

def test_listar_produtos_devolve_seed(client):
    r = client.get("/produtos")
    assert r.status_code == 200
    corpo = r.get_json()
    assert corpo["sucesso"] is True
    assert len(corpo["dados"]) == 10
    nomes = {p["nome"] for p in corpo["dados"]}
    assert {"Notebook Gamer", "Cadeira Gamer"} <= nomes


def test_listar_e_buscar_sao_publicos_sem_flags(make_client):
    c = make_client()
    assert c.get("/produtos").status_code == 200
    assert c.get("/produtos/busca?q=Gamer").status_code == 200


def test_buscar_produto_por_id_devolve_campos(client):
    r = client.get("/produtos/1")
    assert r.status_code == 200
    corpo = r.get_json()
    assert corpo["sucesso"] is True
    p = corpo["dados"]
    assert p["nome"] == "Notebook Gamer"
    assert p["preco"] == 5999.99
    assert p["estoque"] == 10
    assert p["categoria"] == "informatica"
    assert {"id", "descricao", "ativo", "criado_em"} <= set(p)


def test_buscar_produto_inexistente_devolve_404(client):
    r = client.get("/produtos/999")
    assert r.status_code == 404
    corpo = r.get_json()
    assert "erro" in corpo
    assert corpo["sucesso"] is False


def test_busca_filtra_por_termo(client):
    r = client.get("/produtos/busca?q=Gamer")
    assert r.status_code == 200
    corpo = r.get_json()
    assert corpo["sucesso"] is True
    assert corpo["total"] == 3
    assert {p["nome"] for p in corpo["dados"]} == {"Notebook Gamer", "Headset Gamer", "Cadeira Gamer"}


def test_busca_filtra_por_categoria(client):
    corpo = client.get("/produtos/busca?categoria=moveis").get_json()
    assert corpo["total"] == 1
    assert corpo["dados"][0]["nome"] == "Cadeira Gamer"


def test_busca_filtra_por_faixa_de_preco(client):
    corpo = client.get("/produtos/busca?preco_min=1000&preco_max=2000").get_json()
    assert {p["nome"] for p in corpo["dados"]} == {"Monitor 27''", "Cadeira Gamer"}
    assert corpo["total"] == 2


def test_busca_sem_resultado_devolve_total_zero(client):
    corpo = client.get("/produtos/busca?q=inexistentexyz").get_json()
    assert corpo["total"] == 0
    assert corpo["dados"] == []


def test_criar_produto_e_buscar_devolve_campos(client):
    r = client.post("/produtos", json=NOVO)
    assert r.status_code == 201
    corpo = r.get_json()
    assert corpo["sucesso"] is True
    assert "mensagem" in corpo
    novo_id = corpo["dados"]["id"]
    p = client.get(f"/produtos/{novo_id}").get_json()["dados"]
    for campo in ("nome", "descricao", "preco", "estoque", "categoria"):
        assert p[campo] == NOVO[campo]


def test_criar_produto_sem_categoria_usa_geral(client):
    dados = {k: v for k, v in NOVO.items() if k != "categoria"}
    novo_id = client.post("/produtos", json=dados).get_json()["dados"]["id"]
    assert client.get(f"/produtos/{novo_id}").get_json()["dados"]["categoria"] == "geral"


@pytest.mark.parametrize("faltando", ["nome", "preco", "estoque"])
def test_criar_produto_sem_campo_obrigatorio_devolve_400(client, faltando):
    dados = {k: v for k, v in NOVO.items() if k != faltando}
    r = client.post("/produtos", json=dados)
    assert r.status_code == 400
    assert "erro" in r.get_json()


@pytest.mark.parametrize("campo,valor", [
    ("preco", -1), ("estoque", -1), ("nome", "A"), ("nome", "x" * 201), ("categoria", "brinquedos"),
])
def test_criar_produto_invalido_devolve_400(client, campo, valor):
    r = client.post("/produtos", json={**NOVO, campo: valor})
    assert r.status_code == 400
    assert "erro" in r.get_json()
    assert len(client.get("/produtos").get_json()["dados"]) == 10


def test_atualizar_produto_altera_campos(client):
    dados = {**NOVO, "nome": "Notebook Atualizado"}
    r = client.put("/produtos/1", json=dados)
    assert r.status_code == 200
    corpo = r.get_json()
    assert corpo["sucesso"] is True
    assert "mensagem" in corpo
    p = client.get("/produtos/1").get_json()["dados"]
    assert p["nome"] == "Notebook Atualizado"
    assert p["preco"] == NOVO["preco"]
    assert p["categoria"] == "livros"


def test_atualizar_produto_inexistente_devolve_404(client):
    r = client.put("/produtos/999", json=NOVO)
    assert r.status_code == 404
    assert "erro" in r.get_json()


@pytest.mark.parametrize("campo,valor", [("preco", -1), ("estoque", -5)])
def test_atualizar_produto_com_negativo_devolve_400(client, campo, valor):
    r = client.put("/produtos/1", json={**NOVO, campo: valor})
    assert r.status_code == 400
    assert "erro" in r.get_json()
    assert client.get("/produtos/1").get_json()["dados"]["nome"] == "Notebook Gamer"


def test_atualizar_produto_sem_campo_obrigatorio_devolve_400(client):
    r = client.put("/produtos/1", json={"nome": "Sem preco"})
    assert r.status_code == 400
    assert "erro" in r.get_json()


def test_deletar_produto_remove(client, query_db):
    r = client.delete("/produtos/10")
    assert r.status_code == 200
    corpo = r.get_json()
    assert corpo["sucesso"] is True
    assert "mensagem" in corpo
    assert client.get("/produtos/10").status_code == 404
    assert query_db("SELECT COUNT(*) AS n FROM produtos WHERE id = 10")[0]["n"] == 0


def test_deletar_produto_inexistente_devolve_404(client):
    r = client.delete("/produtos/999")
    assert r.status_code == 404
    assert "erro" in r.get_json()


# ---------------------------------------------------------------- comportamento novo

ESCRITAS = [
    ("post", "/produtos", NOVO),
    ("put", "/produtos/1", NOVO),
    ("delete", "/produtos/1", None),
]


@pytest.mark.parametrize("metodo,url,corpo", ESCRITAS)
def test_escrita_de_produto_sem_flag_devolve_403(make_client, query_db, metodo, url, corpo):
    # comportamento novo
    c = make_client()
    r = getattr(c, metodo)(url, json=corpo) if corpo else getattr(c, metodo)(url)
    assert r.status_code == 403
    assert query_db("SELECT nome FROM produtos WHERE id = 1")[0]["nome"] == "Notebook Gamer"


@pytest.mark.parametrize("metodo,url,corpo", ESCRITAS)
def test_escrita_de_produto_sem_token_devolve_401(make_client, metodo, url, corpo):
    # comportamento novo
    c = make_client(flags=True, enviar_token=False)
    r = getattr(c, metodo)(url, json=corpo) if corpo else getattr(c, metodo)(url)
    assert r.status_code == 401


def test_busca_com_preco_min_invalido_devolve_400(client):
    # comportamento novo
    r = client.get("/produtos/busca?preco_min=abc")
    assert r.status_code == 400
    assert "erro" in r.get_json()


@pytest.mark.parametrize("campo,valor", [("preco", "abc"), ("estoque", "x")])
def test_criar_produto_com_numero_invalido_devolve_400(client, campo, valor):
    # comportamento novo
    r = client.post("/produtos", json={**NOVO, campo: valor})
    assert r.status_code == 400
    assert "erro" in r.get_json()


def test_atualizar_produto_com_categoria_invalida_devolve_400(client):
    # comportamento novo
    r = client.put("/produtos/1", json={**NOVO, "categoria": "brinquedos"})
    assert r.status_code == 400
    assert "erro" in r.get_json()
    assert client.get("/produtos/1").get_json()["dados"]["categoria"] == "informatica"


def test_atualizar_produto_com_nome_curto_devolve_400(client):
    # comportamento novo
    r = client.put("/produtos/1", json={**NOVO, "nome": "A"})
    assert r.status_code == 400
    assert "erro" in r.get_json()
    assert client.get("/produtos/1").get_json()["dados"]["nome"] == "Notebook Gamer"


def test_criar_produto_com_aspas_no_nome_preserva_nome(client):
    # comportamento novo
    r = client.post("/produtos", json={**NOVO, "nome": "Livro d'Água"})
    assert r.status_code == 201
    novo_id = r.get_json()["dados"]["id"]
    assert client.get(f"/produtos/{novo_id}").get_json()["dados"]["nome"] == "Livro d'Água"


def test_busca_com_injecao_sql_nao_devolve_produtos(client):
    # comportamento novo
    r = client.get("/produtos/busca", query_string={"q": "' OR 1=1 --"})
    assert r.status_code == 200
    assert r.get_json()["total"] == 0
