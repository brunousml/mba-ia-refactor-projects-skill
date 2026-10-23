"""Testes do domínio /produtos.

Bloco A: caracterização do comportamento original (passa antes e depois da refatoração).
Bloco B: comportamento novo (guards por flag/token e correções); falha no original.
"""
import pytest

CORPO_VALIDO = {
    "nome": "Cadeira Ergonômica",
    "descricao": "Cadeira de escritório",
    "preco": 899.9,
    "estoque": 7,
    "categoria": "moveis",
}


def corpo(**mudancas):
    novo = dict(CORPO_VALIDO)
    novo.update(mudancas)
    return novo


def corpo_sem(campo):
    novo = dict(CORPO_VALIDO)
    novo.pop(campo)
    return novo


def criar(cliente, **mudancas):
    resposta = cliente.post("/produtos", json=corpo(**mudancas))
    assert resposta.status_code == 201
    return resposta.get_json()["dados"]["id"]


# ---------------------------------------------------------------- A) caracterização


def test_listar_produtos_retorna_10_itens(cliente):
    resposta = cliente.get("/produtos")
    json = resposta.get_json()
    assert resposta.status_code == 200
    assert json["sucesso"] is True
    assert isinstance(json["dados"], list)
    assert len(json["dados"]) == 10


def test_buscar_produto_por_id_retorna_notebook_gamer(cliente):
    resposta = cliente.get("/produtos/1")
    assert resposta.status_code == 200
    assert resposta.get_json()["dados"]["nome"] == "Notebook Gamer"


def test_buscar_produto_inexistente_retorna_404(cliente):
    resposta = cliente.get("/produtos/999")
    assert resposta.status_code == 404
    assert resposta.get_json()["erro"] == "Produto não encontrado"


def test_busca_por_texto_mouse_retorna_um_resultado(cliente):
    resposta = cliente.get("/produtos/busca?q=Mouse")
    json = resposta.get_json()
    assert resposta.status_code == 200
    assert json["total"] == 1
    assert json["dados"][0]["nome"] == "Mouse Wireless"


def test_busca_por_categoria_e_faixa_de_preco_filtra_itens(cliente):
    resposta = cliente.get("/produtos/busca?categoria=informatica&preco_min=100&preco_max=2000")
    json = resposta.get_json()
    assert resposta.status_code == 200
    assert json["dados"]
    for item in json["dados"]:
        assert item["categoria"] == "informatica"
        assert 100 <= item["preco"] <= 2000


def test_criar_produto_valido_retorna_201_e_pode_ser_lido(cliente):
    resposta = cliente.post("/produtos", json=corpo())
    json = resposta.get_json()
    assert resposta.status_code == 201
    assert isinstance(json["dados"]["id"], int)
    assert json["mensagem"] == "Produto criado"
    lido = cliente.get(f"/produtos/{json['dados']['id']}")
    assert lido.status_code == 200
    assert lido.get_json()["dados"]["nome"] == CORPO_VALIDO["nome"]


def test_criar_produto_sem_nome_retorna_400(cliente):
    resposta = cliente.post("/produtos", json=corpo_sem("nome"))
    assert resposta.status_code == 400
    assert resposta.get_json()["erro"] == "Nome é obrigatório"


def test_criar_produto_com_preco_negativo_retorna_400(cliente):
    resposta = cliente.post("/produtos", json=corpo(preco=-1))
    assert resposta.status_code == 400
    assert resposta.get_json()["erro"] == "Preço não pode ser negativo"


def test_criar_produto_com_nome_de_um_caractere_retorna_400(cliente):
    resposta = cliente.post("/produtos", json=corpo(nome="A"))
    assert resposta.status_code == 400
    assert resposta.get_json()["erro"] == "Nome muito curto"


def test_criar_produto_com_categoria_invalida_retorna_400(cliente):
    resposta = cliente.post("/produtos", json=corpo(categoria="xyz"))
    assert resposta.status_code == 400
    assert resposta.get_json()["erro"].startswith("Categoria inválida")


def test_atualizar_produto_valido_reflete_novo_nome(cliente):
    id_ = criar(cliente)
    resposta = cliente.put(f"/produtos/{id_}", json=corpo(nome="Cadeira Nova"))
    assert resposta.status_code == 200
    assert cliente.get(f"/produtos/{id_}").get_json()["dados"]["nome"] == "Cadeira Nova"


def test_atualizar_produto_inexistente_retorna_404(cliente):
    resposta = cliente.put("/produtos/999", json=corpo())
    assert resposta.status_code == 404


def test_atualizar_produto_sem_preco_retorna_400(cliente):
    id_ = criar(cliente)
    resposta = cliente.put(f"/produtos/{id_}", json=corpo_sem("preco"))
    assert resposta.status_code == 400
    assert resposta.get_json()["erro"] == "Preço é obrigatório"


def test_deletar_produto_valido_retorna_200_e_depois_404(cliente):
    id_ = criar(cliente)
    resposta = cliente.delete(f"/produtos/{id_}")
    assert resposta.status_code == 200
    assert resposta.get_json()["mensagem"] == "Produto deletado"
    assert cliente.get(f"/produtos/{id_}").status_code == 404


def test_deletar_produto_inexistente_retorna_404(cliente):
    assert cliente.delete("/produtos/999").status_code == 404


@pytest.mark.parametrize("caminho", ["/produtos", "/produtos/1"])
def test_leitura_de_produtos_e_publica_sem_flags(cliente_sem_flags, caminho):
    assert cliente_sem_flags.get(caminho).status_code == 200


# ------------------------------------------------- B) comportamento novo (guards)


def test_criar_produto_sem_flags_retorna_403(cliente_sem_flags):
    resposta = cliente_sem_flags.post("/produtos", json=corpo())
    assert resposta.status_code == 403
    assert resposta.get_json()["erro"] == "Recurso desabilitado"


def test_atualizar_produto_sem_flags_retorna_403(cliente_sem_flags):
    resposta = cliente_sem_flags.put("/produtos/1", json=corpo())
    assert resposta.status_code == 403
    assert resposta.get_json()["erro"] == "Recurso desabilitado"


def test_deletar_produto_sem_flags_retorna_403(cliente_sem_flags):
    resposta = cliente_sem_flags.delete("/produtos/1")
    assert resposta.status_code == 403
    assert resposta.get_json()["erro"] == "Recurso desabilitado"


def test_criar_produto_com_flag_de_escrita_e_sem_token_retorna_401(montar):
    cliente = montar(flags=("ENABLE_WRITE_ROUTES",))
    resposta = cliente.post("/produtos", json=corpo())
    assert resposta.status_code == 401
    assert resposta.get_json()["erro"] == "Não autorizado"


def test_criar_produto_com_flag_de_escrita_e_token_errado_retorna_401(montar):
    cliente = montar(flags=("ENABLE_WRITE_ROUTES",), token_enviado="token-errado")
    resposta = cliente.post("/produtos", json=corpo())
    assert resposta.status_code == 401
    assert resposta.get_json()["erro"] == "Não autorizado"


def test_flag_de_leitura_sensivel_nao_libera_escrita_de_produto(montar):
    cliente = montar(flags=("ENABLE_SENSITIVE_READS",), token_enviado="token-de-teste")
    resposta = cliente.post("/produtos", json=corpo())
    assert resposta.status_code == 403


@pytest.mark.parametrize(
    "metodo, caminho, enviar_corpo, status_esperado",
    [
        ("post", "/produtos", True, 201),
        ("put", "/produtos/1", True, 200),
        ("delete", "/produtos/1", False, 200),
    ],
)
def test_escrita_com_flag_ligada_e_token_certo_mantem_status_original(
    montar, metodo, caminho, enviar_corpo, status_esperado
):
    cliente = montar(flags=("ENABLE_WRITE_ROUTES",), token_enviado="token-de-teste")
    kwargs = {"json": corpo()} if enviar_corpo else {}
    resposta = getattr(cliente, metodo)(caminho, **kwargs)
    assert resposta.status_code == status_esperado


# ------------------------------------------------- B) comportamento novo (correções)


def test_criar_produto_com_aspas_simples_no_nome_retorna_201(cliente):
    nome = "Mouse 'Gamer'"
    resposta = cliente.post("/produtos", json=corpo(nome=nome))
    assert resposta.status_code == 201
    id_ = resposta.get_json()["dados"]["id"]
    assert cliente.get(f"/produtos/{id_}").get_json()["dados"]["nome"] == nome


def test_busca_com_injecao_de_sql_retorna_zero_resultados(cliente):
    resposta = cliente.get("/produtos/busca", query_string={"q": "' OR '1'='1"})
    assert resposta.status_code == 200
    assert resposta.get_json()["total"] == 0


def test_busca_com_preco_min_invalido_retorna_400(cliente):
    resposta = cliente.get("/produtos/busca?preco_min=abc")
    assert resposta.status_code == 400


def test_atualizar_produto_com_categoria_invalida_retorna_400(cliente):
    resposta = cliente.put("/produtos/1", json=corpo(categoria="xyz"))
    assert resposta.status_code == 400
    assert "Categoria inválida" in resposta.get_json()["erro"]


def test_atualizar_produto_com_nome_de_um_caractere_retorna_400(cliente):
    resposta = cliente.put("/produtos/1", json=corpo(nome="A"))
    assert resposta.status_code == 400


def test_criar_produto_sem_corpo_json_retorna_400(cliente):
    resposta = cliente.post("/produtos", data="", content_type="application/json")
    assert resposta.status_code == 400
