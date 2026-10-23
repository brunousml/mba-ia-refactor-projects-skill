"""Testes do domínio CATEGORIES (escritos antes da refatoração).

Caracterização: verdes no código original.
new_behavior: especificação do refatorado (T08 guards e T17 validação).
"""
import pytest

from models.category import Category
from models.task import Task

KEYS = {"id", "name", "description", "color", "created_at", "task_count"}
NULL_JSON = dict(data="null", content_type="application/json")


def _by_id(resp):
    return {c["id"]: c for c in resp.get_json()}


# ---------------------------------------------------------------- caracterização

def test_list_categories_returns_four_with_keys(client):
    resp = client.get("/categories")
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body) == 4
    for c in body:
        assert set(c.keys()) == KEYS


def test_list_categories_names_and_task_count(client):
    cats = _by_id(client.get("/categories"))
    assert {i: c["name"] for i, c in cats.items()} == {
        1: "Backend", 2: "Frontend", 3: "DevOps", 4: "Bug"}
    assert {i: c["task_count"] for i, c in cats.items()} == {1: 6, 2: 1, 3: 2, 4: 1}


def test_create_category_defaults(admin_client):
    resp = admin_client.post("/categories", json={"name": "QA"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["name"] == "QA"
    assert body["description"] == ""
    assert body["color"] == "#000000"
    assert isinstance(body["id"], int)
    listed = _by_id(admin_client.get("/categories"))
    assert listed[body["id"]]["task_count"] == 0


def test_create_category_full(admin_client):
    resp = admin_client.post("/categories", json={
        "name": "QA", "description": "Qualidade", "color": "#ABCDEF"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert (body["description"], body["color"]) == ("Qualidade", "#ABCDEF")


def test_create_category_without_name(admin_client):
    resp = admin_client.post("/categories", json={"description": "x"})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "Nome é obrigatório"}


def test_create_category_empty_name(admin_client):
    resp = admin_client.post("/categories", json={"name": ""})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "Nome é obrigatório"}


def test_create_category_null_body(admin_client):
    resp = admin_client.post("/categories", **NULL_JSON)
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "Dados inválidos"}


def test_update_category_partial_keeps_other_fields(admin_client):
    before = _by_id(admin_client.get("/categories"))[2]
    resp = admin_client.put("/categories/2", json={"name": "UI"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["name"] == "UI"
    assert body["description"] == before["description"]
    assert body["color"] == before["color"]
    after = _by_id(admin_client.get("/categories"))[2]
    assert after["name"] == "UI"
    assert after["color"] == before["color"]


def test_update_category_color_valid(admin_client):
    resp = admin_client.put("/categories/1", json={"color": "#123456"})
    assert resp.status_code == 200
    assert resp.get_json()["color"] == "#123456"


def test_update_category_not_found(admin_client):
    resp = admin_client.put("/categories/9999", json={"name": "x"})
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "Categoria não encontrada"}


def test_delete_category(admin_client):
    resp = admin_client.delete("/categories/4")
    assert resp.status_code == 200
    assert resp.get_json() == {"message": "Categoria deletada"}
    cats = _by_id(admin_client.get("/categories"))
    assert 4 not in cats
    assert len(cats) == 3


def test_delete_category_not_found(admin_client):
    resp = admin_client.delete("/categories/9999")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "Categoria não encontrada"}


def test_delete_category_nullifies_task_category(admin_client, db_session):
    """Original: o ORM (relationship sem cascade) zera category_id das tasks;
    as tasks continuam existindo, sem ficar com FK órfã."""
    task_ids = [t.id for t in Task.query.filter_by(category_id=3).all()]
    assert len(task_ids) == 2
    total = Task.query.count()
    assert admin_client.delete("/categories/3").status_code == 200
    db_session.expire_all()
    assert Task.query.count() == total
    for tid in task_ids:
        assert db_session.get(Task, tid).category_id is None
    assert Task.query.filter_by(category_id=3).count() == 0


# ---------------------------------------------------------------- new_behavior

@pytest.mark.new_behavior
def test_create_category_disabled_without_flag(client):
    resp = client.post("/categories", json={"name": "QA"})
    assert resp.status_code == 403
    assert resp.get_json() == {"error": "Recurso desabilitado"}


@pytest.mark.new_behavior
def test_create_category_requires_token(flags_client):
    resp = flags_client.post("/categories", json={"name": "QA"})
    assert resp.status_code == 401
    assert resp.get_json() == {"error": "Não autorizado"}


@pytest.mark.new_behavior
def test_create_category_wrong_token(wrong_token_client):
    resp = wrong_token_client.post("/categories", json={"name": "QA"})
    assert resp.status_code == 401
    assert resp.get_json() == {"error": "Não autorizado"}


@pytest.mark.new_behavior
def test_update_category_disabled_without_flag(client, db_session):
    resp = client.put("/categories/1", json={"name": "Hack"})
    assert resp.status_code == 403
    assert resp.get_json() == {"error": "Recurso desabilitado"}
    db_session.expire_all()
    assert db_session.get(Category, 1).name == "Backend"


@pytest.mark.new_behavior
def test_update_category_requires_token(flags_client, db_session):
    resp = flags_client.put("/categories/1", json={"name": "Hack"})
    assert resp.status_code == 401
    assert resp.get_json() == {"error": "Não autorizado"}
    db_session.expire_all()
    assert db_session.get(Category, 1).name == "Backend"


@pytest.mark.new_behavior
def test_delete_category_disabled_without_flag(client, db_session):
    resp = client.delete("/categories/1")
    assert resp.status_code == 403
    assert resp.get_json() == {"error": "Recurso desabilitado"}
    db_session.expire_all()
    assert db_session.get(Category, 1) is not None


@pytest.mark.new_behavior
def test_delete_category_requires_token(flags_client, db_session):
    resp = flags_client.delete("/categories/1")
    assert resp.status_code == 401
    assert resp.get_json() == {"error": "Não autorizado"}
    db_session.expire_all()
    assert db_session.get(Category, 1) is not None


@pytest.mark.new_behavior
def test_delete_category_wrong_token(wrong_token_client, db_session):
    resp = wrong_token_client.delete("/categories/1")
    assert resp.status_code == 401
    db_session.expire_all()
    assert db_session.get(Category, 1) is not None


@pytest.mark.new_behavior
def test_update_category_null_body(admin_client):
    resp = admin_client.put("/categories/1", **NULL_JSON)
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "Dados inválidos"}


@pytest.mark.new_behavior
def test_create_category_name_not_string(admin_client):
    resp = admin_client.post("/categories", json={"name": 123})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


@pytest.mark.new_behavior
def test_create_category_invalid_color(admin_client):
    resp = admin_client.post("/categories", json={"name": "QA", "color": "azul"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


@pytest.mark.new_behavior
def test_update_category_invalid_color(admin_client, db_session):
    resp = admin_client.put("/categories/1", json={"color": "xyz"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()
    db_session.expire_all()
    assert db_session.get(Category, 1).color != "xyz"
