"""Mapeamento rota -> flag do guard (T08).

Cada rota protegida pertence a exatamente uma flag:
- ENABLE_ADMIN_ROUTES: rotas que apagam ou executam SQL, e o relatório de vendas.
- ENABLE_SENSITIVE_READS: leituras de usuários e pedidos.
- ENABLE_WRITE_ROUTES: criação, alteração e remoção de produtos, usuários e pedidos.

Com uma flag isolada ligada e o token certo, só as rotas dela passam do guard.
Flag desligada devolve 403; flag ligada sem token ou com token errado devolve 401.
"""
import pytest

from tests.conftest import FLAGS, TOKEN, TOKEN_ERRADO

ADMIN, LEITURA, ESCRITA = FLAGS

PEDIDO = {"usuario_id": 2, "itens": [{"produto_id": 1, "quantidade": 1}]}
PRODUTO = {"nome": "Teclado", "descricao": "ABNT2", "preco": 100.0, "estoque": 5, "categoria": "informatica"}
USUARIO = {"nome": "Ana", "email": "ana@example.com", "senha": "segredo123"}

# (flag, método, caminho, corpo JSON ou None)
ROTAS = [
    (ADMIN, "POST", "/admin/reset-db", None),
    (ADMIN, "POST", "/admin/query", {"sql": "SELECT id FROM produtos"}),
    (ADMIN, "GET", "/relatorios/vendas", None),
    (LEITURA, "GET", "/usuarios", None),
    (LEITURA, "GET", "/usuarios/1", None),
    (LEITURA, "GET", "/pedidos", None),
    (LEITURA, "GET", "/pedidos/usuario/2", None),
    (ESCRITA, "POST", "/produtos", PRODUTO),
    (ESCRITA, "PUT", "/produtos/1", PRODUTO),
    (ESCRITA, "DELETE", "/produtos/1", None),
    (ESCRITA, "POST", "/usuarios", USUARIO),
    (ESCRITA, "POST", "/pedidos", PEDIDO),
    (ESCRITA, "PUT", "/pedidos/1/status", {"status": "aprovado"}),
]

IDS = [f"{metodo} {caminho}" for _, metodo, caminho, _ in ROTAS]
COMBINACOES = [(ligada, rota) for ligada in FLAGS for rota in ROTAS]
IDS_COMBINACOES = [f"{ligada}:{metodo} {caminho}" for ligada, (_, metodo, caminho, _) in COMBINACOES]
ROTAS_E_FLAG = [pytest.param(rota, id=id_) for rota, id_ in zip(ROTAS, IDS)]


def chamar(cliente, metodo, caminho, json):
    return cliente.open(caminho, method=metodo, json=json)


def test_as_13_rotas_protegidas_estao_mapeadas():
    assert len(ROTAS) == 13
    assert len({(m, c) for _, m, c, _ in ROTAS}) == 13


@pytest.mark.parametrize("ligada,rota", COMBINACOES, ids=IDS_COMBINACOES)
def test_flag_isolada_libera_so_as_rotas_dela(montar, ligada, rota):
    flag_da_rota, metodo, caminho, json = rota
    cliente = montar(flags=(ligada,), token_enviado=TOKEN)
    resposta = chamar(cliente, metodo, caminho, json)
    if flag_da_rota == ligada:
        assert resposta.status_code not in (401, 403)
    else:
        assert resposta.status_code == 403
        assert resposta.get_json() == {"erro": "Recurso desabilitado"}


@pytest.mark.parametrize("rota", ROTAS_E_FLAG)
def test_flag_ligada_sem_token_devolve_401_com_corpo(montar, rota):
    flag, metodo, caminho, json = rota
    cliente = montar(flags=(flag,), token_enviado=None)
    resposta = chamar(cliente, metodo, caminho, json)
    assert resposta.status_code == 401
    assert resposta.get_json() == {"erro": "Não autorizado"}


@pytest.mark.parametrize("rota", ROTAS_E_FLAG)
def test_flag_ligada_com_token_errado_devolve_401_com_corpo(montar, rota):
    flag, metodo, caminho, json = rota
    cliente = montar(flags=(flag,), token_enviado=TOKEN_ERRADO)
    resposta = chamar(cliente, metodo, caminho, json)
    assert resposta.status_code == 401
    assert resposta.get_json() == {"erro": "Não autorizado"}
