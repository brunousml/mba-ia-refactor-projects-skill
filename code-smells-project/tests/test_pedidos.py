"""Testes do domínio /pedidos.

Bloco A: caracterização do comportamento original (passa antes e depois da refatoração).
Bloco B: comportamento novo (guards, validação de tipos);
falha no original.
"""
import sqlite3
from pathlib import Path

import pytest

from tests.conftest import TOKEN

RAIZ = Path(__file__).resolve().parent.parent
SENHA = "123456"
ITENS_VALIDOS = [
    {"produto_id": 1, "quantidade": 1},
    {"produto_id": 2, "quantidade": 2},
]


def corpo(**mudancas):
    novo = {"usuario_id": 2, "senha": SENHA, "itens": [dict(i) for i in ITENS_VALIDOS]}
    novo.update(mudancas)
    return novo


def corpo_sem(campo):
    novo = corpo()
    novo.pop(campo)
    return novo


def um_item(produto_id, quantidade):
    return [{"produto_id": produto_id, "quantidade": quantidade}]


def listar(cliente):
    resposta = cliente.get("/pedidos")
    assert resposta.status_code == 200
    return resposta.get_json()["dados"]


def estoque(cliente, produto_id):
    return cliente.get(f"/produtos/{produto_id}").get_json()["dados"]["estoque"]


def estoque_no_banco(tmp_path, produto_id):
    con = sqlite3.connect(tmp_path / "loja.db")
    try:
        return con.execute("SELECT estoque FROM produtos WHERE id = ?", (produto_id,)).fetchone()[0]
    finally:
        con.close()


def total_pedidos_no_banco(tmp_path):
    con = sqlite3.connect(tmp_path / "loja.db")
    try:
        return con.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    finally:
        con.close()


# ---------------------------------------------------------------- Bloco A


def test_criar_pedido_valido_retorna_201_com_id_total_e_mensagem(cliente):
    resposta = cliente.post("/pedidos", json=corpo())
    assert resposta.status_code == 201
    json = resposta.get_json()
    assert json["mensagem"] == "Pedido criado com sucesso"
    assert isinstance(json["dados"]["pedido_id"], int)
    assert json["dados"]["total"] == pytest.approx(6179.79)


def test_criar_pedido_baixa_o_estoque_dos_produtos(cliente):
    cliente.post("/pedidos", json=corpo())
    assert estoque(cliente, 1) == 9
    assert estoque(cliente, 2) == 48


def test_listar_pedidos_mostra_pedido_pendente_com_nomes_dos_produtos(cliente):
    cliente.post("/pedidos", json=corpo())
    pedidos = listar(cliente)
    assert len(pedidos) == 1
    assert pedidos[0]["status"] == "pendente"
    nomes = {i["produto_nome"] for i in pedidos[0]["itens"]}
    assert nomes == {"Notebook Gamer", "Mouse Wireless"}


def test_listar_pedidos_do_usuario_2_traz_o_pedido_criado(cliente):
    cliente.post("/pedidos", json=corpo())
    resposta = cliente.get("/pedidos/usuario/2")
    assert resposta.status_code == 200
    dados = resposta.get_json()["dados"]
    assert len(dados) == 1
    assert dados[0]["usuario_id"] == 2


def test_listar_pedidos_de_usuario_sem_pedidos_retorna_lista_vazia(cliente):
    cliente.post("/pedidos", json=corpo())
    resposta = cliente.get("/pedidos/usuario/3")
    assert resposta.status_code == 200
    assert resposta.get_json()["dados"] == []


def test_criar_pedido_sem_usuario_id_retorna_400(cliente):
    resposta = cliente.post("/pedidos", json=corpo_sem("usuario_id"))
    assert resposta.status_code == 400
    assert resposta.get_json()["erro"] == "Usuario ID é obrigatório"


def test_criar_pedido_com_itens_vazios_retorna_400(cliente):
    resposta = cliente.post("/pedidos", json=corpo(itens=[]))
    assert resposta.status_code == 400
    assert resposta.get_json()["erro"] == "Pedido deve ter pelo menos 1 item"


def test_criar_pedido_com_produto_inexistente_retorna_400_e_nao_cria_pedido(cliente):
    resposta = cliente.post("/pedidos", json=corpo(itens=um_item(999, 1)))
    assert resposta.status_code == 400
    assert resposta.get_json()["erro"] == "Produto 999 não encontrado"
    assert listar(cliente) == []


def test_criar_pedido_com_estoque_insuficiente_retorna_400_e_nao_cria_pedido(cliente):
    resposta = cliente.post("/pedidos", json=corpo(itens=um_item(5, 100)))
    assert resposta.status_code == 400
    assert resposta.get_json()["erro"] == "Estoque insuficiente para Headset Gamer"
    assert listar(cliente) == []


def test_atualizar_status_para_aprovado_retorna_200_e_reflete_na_listagem(cliente):
    pedido_id = cliente.post("/pedidos", json=corpo()).get_json()["dados"]["pedido_id"]
    resposta = cliente.put(f"/pedidos/{pedido_id}/status", json={"status": "aprovado"})
    assert resposta.status_code == 200
    assert resposta.get_json()["mensagem"] == "Status atualizado"
    assert listar(cliente)[0]["status"] == "aprovado"


def test_atualizar_status_invalido_retorna_400(cliente):
    pedido_id = cliente.post("/pedidos", json=corpo()).get_json()["dados"]["pedido_id"]
    resposta = cliente.put(f"/pedidos/{pedido_id}/status", json={"status": "invalido"})
    assert resposta.status_code == 400
    assert resposta.get_json()["erro"] == "Status inválido"


# ---------------------------------------------------------------- Bloco B


def test_criar_pedido_sem_flags_retorna_403(cliente_sem_flags):
    resposta = cliente_sem_flags.post("/pedidos", json=corpo())
    assert resposta.status_code == 403
    assert resposta.get_json()["erro"] == "Recurso desabilitado"


def test_criar_pedido_com_flag_de_escrita_e_sem_token_retorna_401(montar):
    cliente = montar(flags=("ENABLE_WRITE_ROUTES",))
    resposta = cliente.post("/pedidos", json=corpo())
    assert resposta.status_code == 401
    assert resposta.get_json()["erro"] == "Não autorizado"


def test_criar_pedido_com_token_errado_retorna_401(montar):
    cliente = montar(flags=("ENABLE_WRITE_ROUTES",), token_enviado="token-errado")
    resposta = cliente.post("/pedidos", json=corpo())
    assert resposta.status_code == 401


def test_listar_pedidos_sem_flags_retorna_403(cliente_sem_flags):
    assert cliente_sem_flags.get("/pedidos").status_code == 403


def test_listar_pedidos_do_usuario_sem_flags_retorna_403(cliente_sem_flags):
    assert cliente_sem_flags.get("/pedidos/usuario/2").status_code == 403


def test_flag_de_escrita_nao_libera_leitura_sensivel_de_pedidos(montar):
    cliente = montar(flags=("ENABLE_WRITE_ROUTES",), token_enviado="token-de-teste")
    assert cliente.get("/pedidos").status_code == 403


def test_atualizar_status_sem_flags_retorna_403(cliente_sem_flags):
    resposta = cliente_sem_flags.put("/pedidos/1/status", json={"status": "aprovado"})
    assert resposta.status_code == 403


def test_criar_pedido_sem_senha_com_flag_e_token_retorna_201_contrato_original(cliente):
    # O contrato original não envia senha. Com o guard de escrita liberado, o pedido é criado.
    resposta = cliente.post("/pedidos", json=corpo_sem("senha"))
    assert resposta.status_code == 201
    assert len(listar(cliente)) == 1


def test_criar_pedido_com_campo_senha_extra_nao_muda_o_contrato(cliente):
    # Campo que o contrato original não define é ignorado: nenhuma credencial é conferida.
    resposta = cliente.post("/pedidos", json=corpo(senha="errada"))
    assert resposta.status_code == 201


def test_criar_pedido_com_quantidade_negativa_retorna_400_e_nao_muda_estoque(cliente, tmp_path):
    resposta = cliente.post("/pedidos", json=corpo(itens=um_item(1, -3)))
    assert resposta.status_code == 400
    assert estoque_no_banco(tmp_path, 1) == 10
    assert total_pedidos_no_banco(tmp_path) == 0


@pytest.mark.parametrize("quantidade", ["2", 1.5])
def test_criar_pedido_com_quantidade_nao_inteira_retorna_400(cliente, quantidade):
    resposta = cliente.post("/pedidos", json=corpo(itens=um_item(1, quantidade)))
    assert resposta.status_code == 400


def test_criar_pedido_com_produto_id_texto_retorna_400_e_nao_grava(cliente, tmp_path):
    resposta = cliente.post("/pedidos", json=corpo(itens=um_item("1 OR 1=1", 1)))
    assert resposta.status_code == 400
    assert total_pedidos_no_banco(tmp_path) == 0


def test_criar_pedido_com_usuario_id_texto_retorna_400_e_nao_grava(cliente, tmp_path):
    resposta = cliente.post("/pedidos", json=corpo(usuario_id="2 OR 1=1"))
    assert resposta.status_code == 400
    assert resposta.get_json() == {"erro": "Usuario ID deve ser inteiro"}
    assert total_pedidos_no_banco(tmp_path) == 0


def test_falha_ao_inserir_item_devolve_500_e_desfaz_pedido_e_estoque(montar, monkeypatch, tmp_path):
    cliente = montar(flags=("ENABLE_WRITE_ROUTES",), token_enviado=TOKEN)
    # O conftest recarrega os módulos em montar(); o patch vem depois, no módulo já importado.
    import models.pedido_model as pedido_model

    original = pedido_model.inserir_item
    chamadas = []

    def inserir_item_quebrado(*args, **kwargs):
        # O 2º item falha: o 1º já gravou o item e baixou o estoque, então o rollback tem trabalho a fazer.
        chamadas.append(args)
        if len(chamadas) == 2:
            raise RuntimeError("falha simulada na inserção do item")
        return original(*args, **kwargs)

    monkeypatch.setattr(pedido_model, "inserir_item", inserir_item_quebrado)

    resposta = cliente.post("/pedidos", json=corpo())

    assert resposta.status_code == 500
    assert resposta.get_json() == {"erro": "Erro interno"}
    assert total_pedidos_no_banco(tmp_path) == 0
    assert len(chamadas) == 2
    assert estoque(cliente, 1) == 10
    assert estoque(cliente, 2) == 50


def test_servico_criar_pedido_sem_credencial_do_dono_cria_o_pedido(montar, monkeypatch):
    cliente = montar(flags=("ENABLE_WRITE_ROUTES",), token_enviado="token-de-teste")
    monkeypatch.syspath_prepend(str(RAIZ))
    from services import pedido_service

    # O banco é acessado pela requisição (flask.g); o serviço roda dentro do contexto da aplicação.
    with cliente.application.app_context():
        resultado = pedido_service.criar_pedido(usuario_id=2, itens=[{"produto_id": 1, "quantidade": 1}])
    assert resultado["pedido_id"] == 1
    assert resultado["total"] == pytest.approx(5999.99)
