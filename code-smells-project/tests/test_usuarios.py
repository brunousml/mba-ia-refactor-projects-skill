"""Testes do domínio de usuários (listagem, busca, cadastro e login).

Grupo A: caracterização do comportamento original (passam antes e depois da refatoração).
Grupo B: comportamento novo decidido na refatoração (falham no original).
"""
import sqlite3

import pytest

TOKEN = "token-de-teste"
TOKEN_ERRADO = "token-errado"
SENHAS_DO_SEED = ("admin123", "123456", "senha123")


def _json(resposta):
    return resposta.get_json()


def _banco(tmp_path):
    return sqlite3.connect(str(tmp_path / "loja.db"))


# ---------------------------------------------------------------- A) caracterização


def test_cadastro_valido_com_flag_de_escrita_retorna_201_com_id_inteiro(cliente):
    resposta = cliente.post(
        "/usuarios", json={"nome": "Ana", "email": "ana@email.com", "senha": "ana123"}
    )
    corpo = _json(resposta)
    assert resposta.status_code == 201
    assert corpo["sucesso"] is True
    assert isinstance(corpo["dados"]["id"], int)


def test_cadastro_sem_senha_e_sem_email_retorna_400(cliente):
    resposta = cliente.post("/usuarios", json={"nome": "Ana"})
    assert resposta.status_code == 400
    assert _json(resposta)["erro"] == "Nome, email e senha são obrigatórios"


def test_listar_usuarios_retorna_tres_itens_com_chaves_esperadas(cliente):
    resposta = cliente.get("/usuarios")
    corpo = _json(resposta)
    assert resposta.status_code == 200
    assert isinstance(corpo["dados"], list)
    assert len(corpo["dados"]) == 3
    for item in corpo["dados"]:
        assert {"id", "nome", "email", "tipo", "criado_em"} <= set(item)


def test_buscar_usuario_existente_retorna_admin(cliente):
    resposta = cliente.get("/usuarios/1")
    assert resposta.status_code == 200
    assert _json(resposta)["dados"]["email"] == "admin@loja.com"


def test_buscar_usuario_inexistente_retorna_404(cliente):
    resposta = cliente.get("/usuarios/999")
    assert resposta.status_code == 404
    assert _json(resposta)["erro"] == "Usuário não encontrado"


def test_login_valido_retorna_dados_do_usuario_sem_senha(cliente_sem_flags):
    resposta = cliente_sem_flags.post(
        "/login", json={"email": "joao@email.com", "senha": "123456"}
    )
    corpo = _json(resposta)
    assert resposta.status_code == 200
    assert corpo["mensagem"] == "Login OK"
    assert corpo["dados"]["id"] == 2
    assert corpo["dados"]["nome"] == "João Silva"
    assert corpo["dados"]["tipo"] == "cliente"
    assert "senha" not in corpo["dados"]


def test_login_com_senha_errada_retorna_401(cliente_sem_flags):
    resposta = cliente_sem_flags.post(
        "/login", json={"email": "joao@email.com", "senha": "errada"}
    )
    assert resposta.status_code == 401
    assert _json(resposta)["erro"] == "Email ou senha inválidos"


def test_login_sem_senha_retorna_400(cliente_sem_flags):
    resposta = cliente_sem_flags.post("/login", json={"email": "joao@email.com"})
    assert resposta.status_code == 400
    assert _json(resposta)["erro"] == "Email e senha são obrigatórios"


def test_usuario_cadastrado_consegue_fazer_login_com_a_mesma_senha(cliente):
    cliente.post(
        "/usuarios", json={"nome": "Ana", "email": "ana@email.com", "senha": "ana123"}
    )
    resposta = cliente.post(
        "/login", json={"email": "ana@email.com", "senha": "ana123"}
    )
    assert resposta.status_code == 200


# ---------------------------------------------------------------- B) comportamento novo


def test_listar_usuarios_sem_flags_retorna_403_recurso_desabilitado(cliente_sem_flags):
    resposta = cliente_sem_flags.get("/usuarios")
    assert resposta.status_code == 403
    assert _json(resposta)["erro"] == "Recurso desabilitado"


def test_buscar_usuario_sem_flags_retorna_403(cliente_sem_flags):
    assert cliente_sem_flags.get("/usuarios/1").status_code == 403


def test_listar_usuarios_com_flag_de_leitura_e_sem_token_retorna_401(montar):
    resposta = montar(flags=("ENABLE_SENSITIVE_READS",)).get("/usuarios")
    assert resposta.status_code == 401
    assert _json(resposta)["erro"] == "Não autorizado"


def test_listar_usuarios_com_flag_de_leitura_e_token_errado_retorna_401(montar):
    resposta = montar(
        flags=("ENABLE_SENSITIVE_READS",), token_enviado=TOKEN_ERRADO
    ).get("/usuarios")
    assert resposta.status_code == 401


def test_flag_de_escrita_nao_libera_leitura_sensivel_de_usuarios(montar):
    resposta = montar(
        flags=("ENABLE_WRITE_ROUTES",), token_enviado=TOKEN
    ).get("/usuarios")
    assert resposta.status_code == 403


def test_listar_usuarios_liberado_nao_expoe_o_campo_senha(montar):
    resposta = montar(
        flags=("ENABLE_SENSITIVE_READS",), token_enviado=TOKEN
    ).get("/usuarios")
    assert resposta.status_code == 200
    itens = _json(resposta)["dados"]
    assert itens
    assert all("senha" not in item for item in itens)


def test_buscar_usuario_liberado_nao_expoe_o_campo_senha(montar):
    resposta = montar(
        flags=("ENABLE_SENSITIVE_READS",), token_enviado=TOKEN
    ).get("/usuarios/1")
    assert resposta.status_code == 200
    assert "senha" not in _json(resposta)["dados"]


def test_senha_cadastrada_nao_fica_em_texto_puro_no_banco(cliente, tmp_path):
    resposta = cliente.post(
        "/usuarios", json={"nome": "Ana", "email": "ana@email.com", "senha": "ana123"}
    )
    assert resposta.status_code == 201
    with _banco(tmp_path) as conexao:
        linhas = conexao.execute("SELECT * FROM usuarios").fetchall()
    valores = [valor for linha in linhas for valor in linha]
    assert "ana123" not in valores


def test_senhas_do_seed_nao_ficam_em_texto_puro_no_banco(cliente_sem_flags, tmp_path):
    cliente_sem_flags.post("/login", json={"email": "joao@email.com", "senha": "x"})
    with _banco(tmp_path) as conexao:
        senhas = [linha[0] for linha in conexao.execute("SELECT senha FROM usuarios")]
    assert len(senhas) == 3
    for senha in senhas:
        assert senha not in SENHAS_DO_SEED


def test_login_com_injecao_sql_retorna_401(cliente_sem_flags):
    resposta = cliente_sem_flags.post("/login", json={"email": "' OR '1'='1' --", "senha": "x"})
    assert resposta.status_code == 401


def test_login_com_corpo_json_lista_retorna_400(cliente_sem_flags):
    resposta = cliente_sem_flags.post("/login", json=[])
    assert resposta.status_code == 400


def test_cadastro_com_apostrofo_no_nome_retorna_201(cliente):
    resposta = cliente.post(
        "/usuarios", json={"nome": "O'Brien", "email": "ob@email.com", "senha": "x1"}
    )
    assert resposta.status_code == 201


def test_cadastro_com_corpo_vazio_retorna_400(cliente):
    resposta = cliente.post(
        "/usuarios", data="", content_type="application/json"
    )
    assert resposta.status_code == 400


def test_cadastro_sem_flags_retorna_403_recurso_desabilitado(cliente_sem_flags):
    resposta = cliente_sem_flags.post(
        "/usuarios", json={"nome": "Ana", "email": "ana@email.com", "senha": "ana123"}
    )
    assert resposta.status_code == 403
    assert _json(resposta)["erro"] == "Recurso desabilitado"


def test_cadastro_com_flag_de_escrita_sem_token_retorna_401(montar):
    resposta = montar(flags=("ENABLE_WRITE_ROUTES",)).post(
        "/usuarios", json={"nome": "Ana", "email": "ana@email.com", "senha": "ana123"}
    )
    assert resposta.status_code == 401


def test_cadastro_com_flag_de_escrita_e_token_errado_retorna_401(montar):
    resposta = montar(flags=("ENABLE_WRITE_ROUTES",), token_enviado="token-errado").post(
        "/usuarios", json={"nome": "Ana", "email": "ana@email.com", "senha": "ana123"}
    )
    assert resposta.status_code == 401


def test_producao_nao_cria_usuarios_de_exemplo(monkeypatch, montar, tmp_path):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "segredo-de-teste")
    cliente = montar()
    assert cliente.post("/login", json={"email": "admin@loja.com", "senha": "admin123"}).status_code == 401
    with _banco(tmp_path) as conexao:
        assert conexao.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0
    assert cliente.get("/produtos").get_json()["dados"]  # o catálogo continua sendo semeado
