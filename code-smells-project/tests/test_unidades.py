"""Testes unitários das camadas novas (serviços, models, utilitários), sem HTTP."""
import pytest


@pytest.fixture
def conn(tmp_path, make_client):
    make_client()  # descarrega módulos antigos e aponta o cwd para tmp_path
    from models.database import Banco

    banco = Banco(str(tmp_path / "unit.db"))
    banco.inicializar()
    conexao = banco.abrir()
    yield conexao
    conexao.close()


def test_hash_de_senha_tem_salt_e_verifica():
    from utils.senha import gerar_hash, verificar_senha

    h1, h2 = gerar_hash("segredo"), gerar_hash("segredo")
    assert h1 != h2 and "segredo" not in h1
    assert verificar_senha("segredo", h1)
    assert not verificar_senha("outra", h1)


def test_verificar_senha_com_formato_inesperado_devolve_false():
    from utils.senha import verificar_senha

    assert verificar_senha("123456", "123456") is False
    assert verificar_senha("x", None) is False


@pytest.mark.parametrize("faturamento,desconto", [
    (0, 0), (1000, 0), (1000.01, 20.0), (5000.01, 250.0), (10000.01, 1000.0),
])
def test_desconto_por_faixa_de_faturamento(faturamento, desconto):
    from services.relatorio_service import calcular_desconto

    assert calcular_desconto(faturamento) == pytest.approx(desconto, abs=0.01)


def test_validar_produto_rejeita_categoria_e_nome_curto():
    from services.erros import ErroDeNegocio
    from services.produto_service import validar_dados_produto

    base = {"nome": "Livro", "preco": 10, "estoque": 1, "categoria": "livros"}
    validar_dados_produto(base)
    for invalido in ({**base, "categoria": "x"}, {**base, "nome": "A"}, {**base, "preco": "abc"}, {**base, "estoque": -1}):
        with pytest.raises(ErroDeNegocio):
            validar_dados_produto(invalido)


def test_criar_pedido_calcula_total_e_baixa_estoque(conn):
    from services import pedido_service

    resultado = pedido_service.criar_pedido(conn, 2, [
        {"produto_id": 1, "quantidade": 2}, {"produto_id": 3, "quantidade": 1},
    ])
    assert resultado["total"] == pytest.approx(5999.99 * 2 + 299.90)
    assert conn.execute("SELECT estoque FROM produtos WHERE id = 1").fetchone()[0] == 8


def test_criar_pedido_sem_estoque_lanca_erro_sem_gravar(conn):
    from services import pedido_service
    from services.erros import ErroDeNegocio

    with pytest.raises(ErroDeNegocio):
        pedido_service.criar_pedido(conn, 2, [{"produto_id": 6, "quantidade": 999}])
    assert conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0] == 0


def test_listar_pedidos_inclui_nome_do_produto_em_lote(conn):
    from models import pedido_model
    from services import pedido_service

    pedido_service.criar_pedido(conn, 2, [{"produto_id": 3, "quantidade": 2}])
    pedidos = pedido_model.listar_pedidos(conn)
    assert pedidos[0]["itens"][0]["produto_nome"] == "Teclado Mecânico"


def test_seed_grava_senha_com_hash(conn):
    from utils.senha import verificar_senha

    senha = conn.execute("SELECT senha FROM usuarios WHERE email = 'joao@email.com'").fetchone()[0]
    assert senha != "123456" and verificar_senha("123456", senha)
