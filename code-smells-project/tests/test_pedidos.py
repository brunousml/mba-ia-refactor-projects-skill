"""Pedidos e relatório: caracterização do contrato original + comportamento novo."""
import pytest

CHAVES_PEDIDO = {"id", "usuario_id", "status", "total", "criado_em", "itens"}
CHAVES_ITEM = {"produto_id", "produto_nome", "quantidade", "preco_unitario"}
CHAVES_RELATORIO = {
    "total_pedidos", "faturamento_bruto", "desconto_aplicavel", "faturamento_liquido",
    "pedidos_pendentes", "pedidos_aprovados", "pedidos_cancelados", "ticket_medio",
}


def _pedido(client, usuario_id=1, itens=None):
    itens = itens if itens is not None else [{"produto_id": 1, "quantidade": 1}]
    return client.post("/pedidos", json={"usuario_id": usuario_id, "itens": itens})


def _estoque(query_db, produto_id):
    return query_db("SELECT estoque FROM produtos WHERE id = ?", (produto_id,))[0]["estoque"]


# ---------------- caracterização: criação ----------------

def test_criar_pedido_retorna_201_com_id_e_total(client):
    resp = _pedido(client, itens=[{"produto_id": 1, "quantidade": 2}, {"produto_id": 3, "quantidade": 3}])
    assert resp.status_code == 201
    dados = resp.get_json()["dados"]
    assert isinstance(dados["pedido_id"], int)
    assert dados["total"] == pytest.approx(5999.99 * 2 + 299.90 * 3)


def test_criar_pedido_baixa_estoque_e_grava_itens(client, query_db):
    resp = _pedido(client, itens=[{"produto_id": 1, "quantidade": 2}, {"produto_id": 4, "quantidade": 5}])
    pedido_id = resp.get_json()["dados"]["pedido_id"]
    assert _estoque(query_db, 1) == 8
    assert _estoque(query_db, 4) == 10
    itens = query_db("SELECT * FROM itens_pedido WHERE pedido_id = ? ORDER BY produto_id", (pedido_id,))
    assert [(i["produto_id"], i["quantidade"]) for i in itens] == [(1, 2), (4, 5)]
    assert itens[0]["preco_unitario"] == pytest.approx(5999.99)
    assert itens[1]["preco_unitario"] == pytest.approx(1899.90)


def test_produto_inexistente_400(client, query_db):
    resp = _pedido(client, itens=[{"produto_id": 9999, "quantidade": 1}])
    assert resp.status_code == 400
    assert query_db("SELECT COUNT(*) AS n FROM pedidos")[0]["n"] == 0


def test_estoque_insuficiente_400_e_estoque_intacto(client, query_db):
    resp = _pedido(client, itens=[{"produto_id": 6, "quantidade": 9}])
    assert resp.status_code == 400
    assert _estoque(query_db, 6) == 8
    assert query_db("SELECT COUNT(*) AS n FROM pedidos")[0]["n"] == 0


def test_itens_vazios_400(client):
    assert _pedido(client, itens=[]).status_code == 400


def test_sem_usuario_id_400(client):
    resp = client.post("/pedidos", json={"itens": [{"produto_id": 1, "quantidade": 1}]})
    assert resp.status_code == 400


# ---------------- caracterização: listagens ----------------

def test_listar_todos_pedidos_formato(client):
    _pedido(client, usuario_id=1, itens=[{"produto_id": 3, "quantidade": 2}])
    resp = client.get("/pedidos")
    assert resp.status_code == 200
    pedidos = resp.get_json()["dados"]
    assert len(pedidos) == 1
    assert set(pedidos[0]) == CHAVES_PEDIDO
    assert pedidos[0]["status"] == "pendente"
    item = pedidos[0]["itens"][0]
    assert set(item) == CHAVES_ITEM
    assert item["produto_id"] == 3
    assert "Teclado" in item["produto_nome"]
    assert item["quantidade"] == 2
    assert item["preco_unitario"] == pytest.approx(299.90)


def test_listar_pedidos_filtra_por_usuario(client):
    _pedido(client, usuario_id=1)
    _pedido(client, usuario_id=2, itens=[{"produto_id": 3, "quantidade": 1}])
    _pedido(client, usuario_id=2, itens=[{"produto_id": 4, "quantidade": 1}])
    pedidos = client.get("/pedidos/usuario/2").get_json()["dados"]
    assert len(pedidos) == 2
    assert all(p["usuario_id"] == 2 for p in pedidos)
    assert set(pedidos[0]) == CHAVES_PEDIDO


def test_usuario_sem_pedidos_lista_vazia(client):
    resp = client.get("/pedidos/usuario/3")
    assert resp.status_code == 200
    assert resp.get_json()["dados"] == []


# ---------------- caracterização: status ----------------

def test_status_valido_200_e_persistido(client, query_db):
    pedido_id = _pedido(client).get_json()["dados"]["pedido_id"]
    resp = client.put(f"/pedidos/{pedido_id}/status", json={"status": "aprovado"})
    assert resp.status_code == 200
    assert query_db("SELECT status FROM pedidos WHERE id = ?", (pedido_id,))[0]["status"] == "aprovado"


def test_status_invalido_400(client, query_db):
    pedido_id = _pedido(client).get_json()["dados"]["pedido_id"]
    resp = client.put(f"/pedidos/{pedido_id}/status", json={"status": "voando"})
    assert resp.status_code == 400
    assert query_db("SELECT status FROM pedidos WHERE id = ?", (pedido_id,))[0]["status"] == "pendente"


# ---------------- caracterização: relatório ----------------

def test_relatorio_vazio_zerado(client):
    resp = client.get("/relatorios/vendas")
    assert resp.status_code == 200
    dados = resp.get_json()["dados"]
    assert set(dados) == CHAVES_RELATORIO
    assert all(v == 0 for v in dados.values())


@pytest.mark.parametrize("itens, taxa", [
    ([{"produto_id": 1, "quantidade": 2}], 0.10),   # 11999.98
    ([{"produto_id": 1, "quantidade": 1}], 0.05),   # 5999.99
    ([{"produto_id": 4, "quantidade": 1}], 0.02),   # 1899.90
    ([{"produto_id": 3, "quantidade": 1}], 0.0),    # 299.90
])
def test_relatorio_faixas_de_desconto(client, itens, taxa):
    total = _pedido(client, itens=itens).get_json()["dados"]["total"]
    dados = client.get("/relatorios/vendas").get_json()["dados"]
    assert dados["faturamento_bruto"] == pytest.approx(total)
    assert dados["desconto_aplicavel"] == pytest.approx(round(total * taxa, 2))
    assert dados["faturamento_liquido"] == pytest.approx(round(total - total * taxa, 2))


def test_relatorio_contagens_por_status_e_ticket(client):
    ids = [_pedido(client, itens=[{"produto_id": 3, "quantidade": 1}]).get_json()["dados"]["pedido_id"]
           for _ in range(4)]
    client.put(f"/pedidos/{ids[0]}/status", json={"status": "aprovado"})
    client.put(f"/pedidos/{ids[1]}/status", json={"status": "cancelado"})
    client.put(f"/pedidos/{ids[2]}/status", json={"status": "enviado"})
    dados = client.get("/relatorios/vendas").get_json()["dados"]
    assert dados["total_pedidos"] == 4
    assert dados["pedidos_pendentes"] == 1
    assert dados["pedidos_aprovados"] == 1
    assert dados["pedidos_cancelados"] == 1
    assert dados["ticket_medio"] == pytest.approx(299.90)


# ---------------- comportamento novo: guards por flag ----------------

@pytest.mark.parametrize("url", ["/pedidos", "/pedidos/usuario/2"])
def test_leitura_sensivel_flag_desligada_403(make_client, url):
    # comportamento novo
    assert make_client().get(url).status_code == 403


@pytest.mark.parametrize("url", ["/pedidos", "/pedidos/usuario/2"])
def test_leitura_sensivel_sem_token_401(make_client, url):
    # comportamento novo
    assert make_client(flags=True, enviar_token=False).get(url).status_code == 401


def _escritas(c):
    return [
        c.post("/pedidos", json={"usuario_id": 1, "itens": [{"produto_id": 1, "quantidade": 1}]}),
        c.put("/pedidos/1/status", json={"status": "aprovado"}),
    ]


def test_escrita_flag_desligada_403(make_client):
    # comportamento novo
    assert [r.status_code for r in _escritas(make_client())] == [403, 403]


def test_escrita_sem_token_401(make_client):
    # comportamento novo
    assert [r.status_code for r in _escritas(make_client(flags=True, enviar_token=False))] == [401, 401]


def test_relatorio_flag_desligada_403(make_client):
    # comportamento novo
    assert make_client().get("/relatorios/vendas").status_code == 403


def test_relatorio_sem_token_401(make_client):
    # comportamento novo
    assert make_client(flags=True, enviar_token=False).get("/relatorios/vendas").status_code == 401


# ---------------- comportamento novo: validação de entrada ----------------

@pytest.mark.parametrize("quantidade", [-3, 0])
def test_quantidade_nao_positiva_400_e_estoque_intacto(client, query_db, quantidade):
    # comportamento novo
    resp = _pedido(client, itens=[{"produto_id": 1, "quantidade": quantidade}])
    assert resp.status_code == 400
    assert _estoque(query_db, 1) == 10


@pytest.mark.parametrize("item", [{"quantidade": 1}, {"produto_id": 1}, {"produto_id": 1, "quantidade": "2"}])
def test_item_malformado_400(client, query_db, item):
    # comportamento novo
    assert _pedido(client, itens=[item]).status_code == 400
    assert _estoque(query_db, 1) == 10


def test_status_sem_corpo_400(client):
    # comportamento novo
    _pedido(client)
    assert client.put("/pedidos/1/status").status_code == 400


def test_usuario_id_nao_inteiro_400(client, query_db):
    # comportamento novo
    resp = _pedido(client, usuario_id="1; DROP TABLE pedidos")
    assert resp.status_code == 400
    assert query_db("SELECT COUNT(*) AS n FROM pedidos")[0]["n"] == 0
