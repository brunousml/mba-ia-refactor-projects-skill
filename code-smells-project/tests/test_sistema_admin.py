"""Testes de sistema (índice, health), relatório de vendas e administração."""
import sqlite3

import pytest

SEGREDO = "minha-chave-super-secreta-123"
SQL_SELECT = {"sql": "SELECT id, nome FROM produtos"}


def _dados(resposta):
    corpo = resposta.get_json()
    return corpo.get("dados", corpo)


def _contar_produtos(tmp_path):
    con = sqlite3.connect(tmp_path / "loja.db")
    try:
        return con.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    finally:
        con.close()


# ---------------------------------------------------------------- A) caracterização


def test_indice_devolve_mensagem_versao_e_endpoints(cliente_sem_flags):
    resposta = cliente_sem_flags.get("/")
    corpo = resposta.get_json()
    assert resposta.status_code == 200
    assert corpo["mensagem"] == "Bem-vindo à API da Loja"
    assert corpo["versao"] == "1.0.0"
    for chave in ("produtos", "usuarios", "pedidos", "login", "relatorios", "health"):
        assert chave in corpo["endpoints"]


def test_health_devolve_status_banco_e_contagens(cliente_sem_flags):
    resposta = cliente_sem_flags.get("/health")
    corpo = resposta.get_json()
    assert resposta.status_code == 200
    assert corpo["status"] == "ok"
    assert corpo["database"] == "connected"
    assert corpo["counts"] == {"produtos": 10, "usuarios": 3, "pedidos": 0}


def test_relatorio_de_vendas_em_banco_sem_pedidos_vem_zerado(cliente):
    resposta = cliente.get("/relatorios/vendas")
    dados = _dados(resposta)
    assert resposta.status_code == 200
    assert dados["total_pedidos"] == 0
    assert dados["faturamento_bruto"] == 0
    assert dados["desconto_aplicavel"] == 0
    assert dados["ticket_medio"] == 0


def test_relatorio_aplica_desconto_de_5_porcento_acima_de_5000(cliente):
    criado = cliente.post(
        "/pedidos",
        json={
            "usuario_id": 2,
            "senha": "123456",
            "itens": [
                {"produto_id": 1, "quantidade": 1},
                {"produto_id": 2, "quantidade": 2},
            ],
        },
    )
    assert criado.status_code == 201

    resposta = cliente.get("/relatorios/vendas")
    dados = _dados(resposta)
    assert resposta.status_code == 200
    assert dados["total_pedidos"] == 1
    assert dados["faturamento_bruto"] == pytest.approx(6179.79, abs=0.01)
    assert dados["desconto_aplicavel"] == pytest.approx(308.99, abs=0.01)
    assert dados["faturamento_liquido"] == pytest.approx(5870.8, abs=0.01)
    assert dados["pedidos_pendentes"] == 1
    assert dados["ticket_medio"] == pytest.approx(6179.79, abs=0.01)


def test_admin_query_select_devolve_lista_de_produtos(cliente):
    resposta = cliente.post("/admin/query", json=SQL_SELECT)
    corpo = resposta.get_json()
    assert resposta.status_code == 200
    assert corpo["sucesso"] is True
    assert len(corpo["dados"]) == 10


def test_admin_query_sem_campo_sql_devolve_400(cliente):
    resposta = cliente.post("/admin/query", json={})
    assert resposta.status_code == 400
    assert resposta.get_json()["erro"] == "Query não informada"


def test_admin_query_delete_em_pedidos_executa(cliente):
    resposta = cliente.post("/admin/query", json={"sql": "DELETE FROM pedidos"})
    corpo = resposta.get_json()
    assert resposta.status_code == 200
    assert corpo["mensagem"] == "Query executada"


def test_admin_reset_db_apaga_os_produtos(cliente):
    resposta = cliente.post("/admin/reset-db")
    assert resposta.status_code == 200
    assert resposta.get_json()["mensagem"] == "Banco de dados resetado"
    assert _dados(cliente.get("/produtos")) == []


def test_admin_query_ligada_com_flag_de_admin_e_token_aceita_select(montar):
    cliente = montar(flags=("ENABLE_ADMIN_ROUTES",), token_enviado="token-de-teste")
    resposta = cliente.post("/admin/query", json=SQL_SELECT)
    assert resposta.status_code == 200
    assert resposta.get_json()["sucesso"] is True


# ---------------------------------------------------------------- B) comportamento novo


def test_health_nao_expoe_a_chave_secreta(cliente_sem_flags):
    resposta = cliente_sem_flags.get("/health")
    assert "secret_key" not in resposta.get_json()
    assert SEGREDO not in resposta.get_data(as_text=True)


def test_health_vem_com_debug_desligado_por_padrao(cliente_sem_flags):
    corpo = cliente_sem_flags.get("/health").get_json()
    assert corpo["debug"] is False


def test_relatorio_com_flag_desligada_devolve_403(cliente_sem_flags):
    resposta = cliente_sem_flags.get("/relatorios/vendas")
    assert resposta.status_code == 403
    assert resposta.get_json()["erro"] == "Recurso desabilitado"


def test_relatorio_sem_token_devolve_401(montar):
    cliente = montar(flags=("ENABLE_ADMIN_ROUTES",))
    resposta = cliente.get("/relatorios/vendas")
    assert resposta.status_code == 401
    assert resposta.get_json()["erro"] == "Não autorizado"


def test_relatorio_com_token_errado_devolve_401(montar):
    cliente = montar(flags=("ENABLE_ADMIN_ROUTES",), token_enviado="token-errado")
    assert cliente.get("/relatorios/vendas").status_code == 401


def test_reset_db_com_flag_desligada_devolve_403_e_preserva_o_banco(cliente_sem_flags, tmp_path):
    resposta = cliente_sem_flags.post("/admin/reset-db")
    assert resposta.status_code == 403
    assert _contar_produtos(tmp_path) == 10


def test_reset_db_sem_token_devolve_401_e_preserva_o_banco(montar, tmp_path):
    cliente = montar(flags=("ENABLE_ADMIN_ROUTES",))
    resposta = cliente.post("/admin/reset-db")
    assert resposta.status_code == 401
    assert _contar_produtos(tmp_path) == 10


def test_admin_query_com_flag_desligada_devolve_403(cliente_sem_flags):
    resposta = cliente_sem_flags.post("/admin/query", json=SQL_SELECT)
    assert resposta.status_code == 403


def test_flag_de_escrita_nao_libera_admin_query(montar):
    cliente = montar(flags=("ENABLE_WRITE_ROUTES",), token_enviado="token-de-teste")
    resposta = cliente.post("/admin/query", json=SQL_SELECT)
    assert resposta.status_code == 403


def test_flag_de_leitura_sensivel_nao_libera_reset_db(montar, tmp_path):
    cliente = montar(flags=("ENABLE_SENSITIVE_READS",), token_enviado="token-de-teste")
    resposta = cliente.post("/admin/reset-db")
    assert resposta.status_code == 403
    assert _contar_produtos(tmp_path) == 10


def test_admin_query_com_erro_de_sql_devolve_erro_interno_generico(montar):
    cliente = montar(flags=("ENABLE_ADMIN_ROUTES",), token_enviado="token-de-teste")
    resposta = cliente.post("/admin/query", json={"sql": "SELECT * FROM nao_existe"})
    assert resposta.status_code == 500
    assert resposta.get_json()["erro"] == "Erro interno"
    assert "no such table" not in resposta.get_data(as_text=True)


def test_cors_nao_libera_origem_arbitraria(cliente_sem_flags):
    atacante = "http://atacante.example"
    resposta = cliente_sem_flags.get("/", headers={"Origin": atacante})
    liberada = resposta.headers.get("Access-Control-Allow-Origin")
    assert liberada not in (atacante, "*")


def test_health_com_banco_padrao_devolve_so_o_nome_do_arquivo(cliente_sem_flags):
    assert cliente_sem_flags.get("/health").get_json()["db_path"] == "loja.db"


def test_health_com_db_path_absoluto_nao_expoe_o_diretorio(montar, monkeypatch, tmp_path):
    caminho = tmp_path / "dados" / "loja.db"
    caminho.parent.mkdir()
    monkeypatch.setenv("DB_PATH", str(caminho))
    cliente = montar()

    resposta = cliente.get("/health")

    assert resposta.status_code == 200
    assert caminho.exists()  # o app realmente usa o arquivo apontado por DB_PATH
    assert resposta.get_json()["db_path"] == "loja.db"
    assert str(tmp_path) not in resposta.get_data(as_text=True)
