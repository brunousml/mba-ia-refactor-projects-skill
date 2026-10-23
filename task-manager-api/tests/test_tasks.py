"""Testes do domínio TASKS.

Caracterização: passam no código original (escritas via admin_client).
new_behavior: contrato novo (guards T08 e 400 no lugar de 500); vermelhos no original.

Seed: 10 tasks; pending=6, in_progress=2, done=1, cancelled=1; atrasadas: ids 1 e 4.
"""
import pytest

from models.task import Task

TASK_KEYS = {"id", "title", "description", "status", "priority", "user_id",
             "category_id", "created_at", "updated_at", "due_date", "tags"}


def _new(**extra):
    body = {"title": "Nova task", "description": "desc", "priority": 2,
            "user_id": 1, "category_id": 1}
    body.update(extra)
    return body


# ---------------------------------------------------------------- GET /tasks

@pytest.mark.parametrize("fx", ["client", "admin_client"])
def test_list_tasks_public(request, fx):
    c = request.getfixturevalue(fx)
    r = c.get("/tasks")
    assert r.status_code == 200
    data = r.get_json()
    assert len(data) == 10
    for t in data:
        assert TASK_KEYS | {"overdue", "user_name", "category_name"} <= set(t)
    by_id = {t["id"]: t for t in data}
    assert by_id[1]["overdue"] is True
    assert by_id[4]["overdue"] is True
    assert sum(1 for t in data if t["overdue"]) == 2
    assert by_id[1]["user_name"] == "João Silva"
    assert by_id[1]["category_name"] == "Backend"
    assert by_id[2]["category_name"] == "Frontend"
    assert by_id[3]["tags"] == ["devops", "ci", "github"]
    assert by_id[1]["tags"] == []


# ------------------------------------------------------------ GET /tasks/<id>

@pytest.mark.parametrize("fx", ["client", "admin_client"])
def test_get_task_ok(request, fx):
    c = request.getfixturevalue(fx)
    r = c.get("/tasks/1")
    assert r.status_code == 200
    d = r.get_json()
    assert TASK_KEYS | {"overdue"} <= set(d)
    assert d["title"] == "Implementar autenticação JWT"
    assert d["overdue"] is True


@pytest.mark.parametrize("fx", ["client", "admin_client"])
def test_get_task_not_overdue(request, fx):
    c = request.getfixturevalue(fx)
    assert c.get("/tasks/2").get_json()["overdue"] is False
    assert c.get("/tasks/6").get_json()["overdue"] is False  # sem due_date


@pytest.mark.parametrize("fx", ["client", "admin_client"])
def test_get_task_not_found(request, fx):
    c = request.getfixturevalue(fx)
    r = c.get("/tasks/9999")
    assert r.status_code == 404
    assert r.get_json() == {"error": "Task não encontrada"}


# --------------------------------------------------------------- POST /tasks

def test_create_task_ok(admin_client):
    r = admin_client.post("/tasks", json=_new(due_date="2030-01-15", tags=["a", "b"]))
    assert r.status_code == 201
    d = r.get_json()
    assert TASK_KEYS <= set(d)
    assert d["title"] == "Nova task"
    assert d["status"] == "pending"
    assert d["priority"] == 2
    assert d["tags"] == ["a", "b"]
    assert d["due_date"].startswith("2030-01-15")
    g = admin_client.get(f"/tasks/{d['id']}")
    assert g.status_code == 200
    assert g.get_json()["tags"] == ["a", "b"]


def test_create_task_defaults(admin_client):
    r = admin_client.post("/tasks", json={"title": "Só título"})
    assert r.status_code == 201
    d = r.get_json()
    assert d["status"] == "pending"
    assert d["priority"] == 3
    assert d["tags"] == []
    assert d["due_date"] is None


def test_create_task_tags_string(admin_client):
    r = admin_client.post("/tasks", json=_new(tags="x,y"))
    assert r.status_code == 201
    assert r.get_json()["tags"] == ["x", "y"]


def test_create_task_persists(admin_client, db_session):
    admin_client.post("/tasks", json=_new())
    assert db_session.query(Task).count() == 11


@pytest.mark.parametrize("body,msg", [
    ({}, "Dados inválidos"),
    ({"description": "x"}, "Título é obrigatório"),
    ({"title": ""}, "Título é obrigatório"),
    ({"title": "ab"}, "Título muito curto"),
    ({"title": "a" * 201}, "Título muito longo"),
    ({"title": "Valida", "status": "xpto"}, "Status inválido"),
    ({"title": "Valida", "priority": 0}, "Prioridade deve ser entre 1 e 5"),
    ({"title": "Valida", "priority": 6}, "Prioridade deve ser entre 1 e 5"),
    ({"title": "Valida", "due_date": "15/01/2030"},
     "Formato de data inválido. Use YYYY-MM-DD"),
])
def test_create_task_validation(admin_client, body, msg):
    r = admin_client.post("/tasks", json=body)
    assert r.status_code == 400
    assert r.get_json() == {"error": msg}


def test_create_task_user_not_found(admin_client):
    r = admin_client.post("/tasks", json=_new(user_id=9999))
    assert r.status_code == 404
    assert r.get_json() == {"error": "Usuário não encontrado"}


def test_create_task_category_not_found(admin_client):
    r = admin_client.post("/tasks", json=_new(category_id=9999))
    assert r.status_code == 404
    assert r.get_json() == {"error": "Categoria não encontrada"}


def test_create_task_validation_does_not_persist(admin_client, db_session):
    admin_client.post("/tasks", json={"title": "ab"})
    assert db_session.query(Task).count() == 10


# ------------------------------------------------------------ PUT /tasks/<id>

def test_update_task_ok(admin_client):
    r = admin_client.put("/tasks/1", json={
        "title": "Título novo", "status": "done", "priority": 5,
        "tags": ["p", "q"], "due_date": "2031-02-03", "user_id": 2,
        "category_id": 2, "description": "nova"})
    assert r.status_code == 200
    d = r.get_json()
    assert TASK_KEYS <= set(d)
    assert d["title"] == "Título novo"
    assert d["status"] == "done"
    assert d["priority"] == 5
    assert d["tags"] == ["p", "q"]
    assert d["due_date"].startswith("2031-02-03")
    assert d["user_id"] == 2 and d["category_id"] == 2
    assert d["description"] == "nova"
    g = admin_client.get("/tasks/1").get_json()
    assert g["title"] == "Título novo"
    assert g["overdue"] is False


def test_update_task_clear_due_date(admin_client):
    r = admin_client.put("/tasks/1", json={"due_date": None})
    assert r.status_code == 200
    assert r.get_json()["due_date"] is None


def test_update_task_not_found(admin_client):
    r = admin_client.put("/tasks/9999", json={"title": "Qualquer"})
    assert r.status_code == 404
    assert r.get_json() == {"error": "Task não encontrada"}


@pytest.mark.parametrize("body,msg", [
    ({}, "Dados inválidos"),
    ({"title": "ab"}, "Título muito curto"),
    ({"title": "a" * 201}, "Título muito longo"),
    ({"status": "xpto"}, "Status inválido"),
    ({"priority": 0}, "Prioridade deve ser entre 1 e 5"),
    ({"priority": 9}, "Prioridade deve ser entre 1 e 5"),
    ({"due_date": "03-02-2031"}, "Formato de data inválido"),
])
def test_update_task_validation(admin_client, body, msg):
    r = admin_client.put("/tasks/1", json=body)
    assert r.status_code == 400
    assert r.get_json() == {"error": msg}


def test_update_task_user_not_found(admin_client):
    r = admin_client.put("/tasks/1", json={"user_id": 9999})
    assert r.status_code == 404
    assert r.get_json() == {"error": "Usuário não encontrado"}


def test_update_task_category_not_found(admin_client):
    r = admin_client.put("/tasks/1", json={"category_id": 9999})
    assert r.status_code == 404
    assert r.get_json() == {"error": "Categoria não encontrada"}


# --------------------------------------------------------- DELETE /tasks/<id>

def test_delete_task_ok(admin_client):
    r = admin_client.delete("/tasks/3")
    assert r.status_code == 200
    assert r.get_json() == {"message": "Task deletada com sucesso"}
    assert admin_client.get("/tasks/3").status_code == 404


def test_delete_task_not_found(admin_client):
    r = admin_client.delete("/tasks/9999")
    assert r.status_code == 404
    assert r.get_json() == {"error": "Task não encontrada"}


# --------------------------------------------------------- GET /tasks/search

@pytest.mark.parametrize("fx", ["client", "admin_client"])
def test_search_by_q_title(request, fx):
    c = request.getfixturevalue(fx)
    r = c.get("/tasks/search?q=Configurar")
    assert r.status_code == 200
    assert {t["id"] for t in r.get_json()} == {3, 9}
    assert TASK_KEYS <= set(r.get_json()[0])


@pytest.mark.parametrize("fx", ["client", "admin_client"])
def test_search_by_q_description(request, fx):
    c = request.getfixturevalue(fx)
    r = c.get("/tasks/search?q=Grafana")
    assert [t["id"] for t in r.get_json()] == [9]


@pytest.mark.parametrize("fx", ["client", "admin_client"])
def test_search_filters(request, fx):
    c = request.getfixturevalue(fx)
    assert len(c.get("/tasks/search?status=pending").get_json()) == 6
    assert {t["id"] for t in c.get("/tasks/search?priority=1").get_json()} == {1, 4}
    assert {t["id"] for t in c.get("/tasks/search?user_id=1").get_json()} == {1, 4, 5, 10}
    combo = c.get("/tasks/search?status=pending&priority=1&user_id=1").get_json()
    assert {t["id"] for t in combo} == {1, 4}
    assert len(c.get("/tasks/search").get_json()) == 10
    assert c.get("/tasks/search?q=naoexiste").get_json() == []


# ---------------------------------------------------------- GET /tasks/stats

@pytest.mark.parametrize("fx", ["client", "admin_client"])
def test_stats(request, fx):
    c = request.getfixturevalue(fx)
    r = c.get("/tasks/stats")
    assert r.status_code == 200
    assert r.get_json() == {
        "total": 10, "pending": 6, "in_progress": 2, "done": 1,
        "cancelled": 1, "overdue": 2, "completion_rate": 10.0,
    }


def test_stats_after_update(admin_client):
    admin_client.put("/tasks/1", json={"status": "done"})
    d = admin_client.get("/tasks/stats").get_json()
    assert d["done"] == 2
    assert d["overdue"] == 1
    assert d["completion_rate"] == round(2 / 10 * 100, 2)


# ===================================================== COMPORTAMENTO NOVO (T08)

@pytest.mark.new_behavior
def test_post_disabled_without_flag(client, db_session):
    r = client.post("/tasks", json=_new())
    assert r.status_code == 403
    assert r.get_json() == {"error": "Recurso desabilitado"}
    assert db_session.query(Task).count() == 10


@pytest.mark.new_behavior
def test_post_requires_token(flags_client):
    r = flags_client.post("/tasks", json=_new())
    assert r.status_code == 401
    assert r.get_json() == {"error": "Não autorizado"}


@pytest.mark.new_behavior
def test_post_wrong_token(wrong_token_client):
    r = wrong_token_client.post("/tasks", json=_new())
    assert r.status_code == 401
    assert r.get_json() == {"error": "Não autorizado"}


@pytest.mark.new_behavior
def test_put_disabled_without_flag(client):
    r = client.put("/tasks/1", json={"title": "Alterado"})
    assert r.status_code == 403
    assert r.get_json() == {"error": "Recurso desabilitado"}


@pytest.mark.new_behavior
def test_put_requires_token(flags_client):
    r = flags_client.put("/tasks/1", json={"title": "Alterado"})
    assert r.status_code == 401
    assert r.get_json() == {"error": "Não autorizado"}


@pytest.mark.new_behavior
def test_put_wrong_token(wrong_token_client):
    r = wrong_token_client.put("/tasks/1", json={"title": "Alterado"})
    assert r.status_code == 401


@pytest.mark.new_behavior
@pytest.mark.parametrize("fx,status,body", [
    ("client", 403, {"error": "Recurso desabilitado"}),
    ("flags_client", 401, {"error": "Não autorizado"}),
    ("wrong_token_client", 401, {"error": "Não autorizado"}),
])
def test_delete_guarded(request, db_session, fx, status, body):
    c = request.getfixturevalue(fx)
    r = c.delete("/tasks/1")
    assert r.status_code == status
    assert r.get_json() == body
    db_session.expire_all()
    assert db_session.get(Task, 1) is not None


# ============================================== COMPORTAMENTO NOVO (T17: 400)

@pytest.mark.new_behavior
def test_post_priority_string(admin_client):
    r = admin_client.post("/tasks", json=_new(priority="alta"))
    assert r.status_code == 400
    assert r.get_json() == {"error": "Prioridade deve ser entre 1 e 5"}


@pytest.mark.new_behavior
def test_post_priority_bool(admin_client):
    r = admin_client.post("/tasks", json=_new(priority=True))
    assert r.status_code == 400
    assert "error" in r.get_json()


@pytest.mark.new_behavior
def test_post_title_not_string(admin_client):
    r = admin_client.post("/tasks", json=_new(title=123))
    assert r.status_code == 400
    assert "error" in r.get_json()


@pytest.mark.new_behavior
def test_post_tags_invalid_type(admin_client):
    r = admin_client.post("/tasks", json=_new(tags=123))
    assert r.status_code == 400
    assert "error" in r.get_json()


@pytest.mark.new_behavior
def test_put_priority_string(admin_client):
    r = admin_client.put("/tasks/1", json={"priority": "x"})
    assert r.status_code == 400
    assert "error" in r.get_json()


@pytest.mark.new_behavior
def test_put_title_not_string(admin_client):
    r = admin_client.put("/tasks/1", json={"title": 12345})
    assert r.status_code == 400
    assert "error" in r.get_json()


@pytest.mark.new_behavior
@pytest.mark.parametrize("qs", ["priority=abc", "user_id=abc"])
def test_search_invalid_int(client, qs):
    r = client.get(f"/tasks/search?{qs}")
    assert r.status_code == 400
    assert "error" in r.get_json()
