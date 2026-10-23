"""Mapeamento flag -> rotas (T08): cada flag guarda exatamente o seu conjunto de rotas.

Liga UMA flag por vez, com ADMIN_TOKEN e X-Admin-Token corretos. As rotas da flag
ligada não podem responder 403 "Recurso desabilitado"; as das outras duas têm de responder.
"""
import pytest

from tests.conftest import ADMIN_TOKEN, FLAGS

pytestmark = pytest.mark.new_behavior

DENIED = {"error": "Recurso desabilitado"}

ROTAS_POR_FLAG = {
    "ENABLE_ADMIN_ROUTES": [
        ("DELETE", "/tasks/1"),
        ("DELETE", "/users/2"),
        ("DELETE", "/categories/1"),
        ("GET", "/reports/summary"),
        ("GET", "/reports/user/1"),
    ],
    "ENABLE_SENSITIVE_READS": [
        ("GET", "/users"),
        ("GET", "/users/1"),
    ],
    "ENABLE_WRITE_ROUTES": [
        ("POST", "/tasks"),
        ("PUT", "/tasks/1"),
        ("POST", "/users"),
        ("PUT", "/users/2"),
        ("POST", "/categories"),
        ("PUT", "/categories/1"),
    ],
}


def _chamar(app, metodo, caminho):
    client = app.test_client()
    kwargs = {"headers": {"X-Admin-Token": ADMIN_TOKEN}}
    if metodo in ("POST", "PUT"):
        kwargs["json"] = {}
    return client.open(caminho, method=metodo, **kwargs)


def _desabilitada(resp):
    return resp.status_code == 403 and resp.get_json() == DENIED


def test_mapeamento_cobre_as_tres_flags():
    assert set(ROTAS_POR_FLAG) == set(FLAGS)


@pytest.mark.parametrize("flag", FLAGS)
def test_flag_isolada_libera_so_as_suas_rotas(app, flag):
    app.config[flag] = True

    for metodo, caminho in ROTAS_POR_FLAG[flag]:
        resp = _chamar(app, metodo, caminho)
        assert not _desabilitada(resp), (
            f"{metodo} {caminho} deveria passar do guard com {flag} ligada "
            f"(status {resp.status_code}, corpo {resp.get_json()})"
        )

    for outra, rotas in ROTAS_POR_FLAG.items():
        if outra == flag:
            continue
        for metodo, caminho in rotas:
            resp = _chamar(app, metodo, caminho)
            assert resp.status_code == 403, (
                f"{metodo} {caminho} deveria dar 403 com só {flag} ligada "
                f"(status {resp.status_code})"
            )
            assert resp.get_json() == DENIED
