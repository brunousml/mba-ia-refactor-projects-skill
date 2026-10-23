"""Reports e sistema/config: caracterização (verde no original) + new_behavior."""
import importlib
import os
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _users(client):
    s = client.get("/reports/summary").get_json()
    return {u["user_name"]: u for u in s["user_productivity"]}


# ---------------------------------------------------------------- caracterização

def test_index(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.get_json() == {"message": "Task Manager API", "version": "1.0"}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "ok"
    assert "timestamp" in body


def test_rota_inexistente_404(client):
    assert client.get("/nao-existe").status_code == 404


def test_summary_estrutura_e_valores(admin_client):
    r = admin_client.get("/reports/summary")
    assert r.status_code == 200
    s = r.get_json()
    assert set(s) == {"generated_at", "overview", "tasks_by_status", "tasks_by_priority",
                      "overdue", "recent_activity", "user_productivity"}
    assert s["overview"] == {"total_tasks": 10, "total_users": 3, "total_categories": 4}
    assert s["tasks_by_status"] == {"pending": 6, "in_progress": 2, "done": 1, "cancelled": 1}
    assert s["tasks_by_priority"] == {"critical": 2, "high": 3, "medium": 3, "low": 2, "minimal": 0}
    assert s["recent_activity"] == {"tasks_created_last_7_days": 10, "tasks_completed_last_7_days": 1}


def test_summary_overdue(admin_client):
    o = admin_client.get("/reports/summary").get_json()["overdue"]
    assert o["count"] == 2
    by_title = {t["title"]: t for t in o["tasks"]}
    assert set(by_title) == {"Implementar autenticação JWT", "Corrigir bug no filtro de busca"}
    for t in o["tasks"]:
        assert set(t) == {"id", "title", "due_date", "days_overdue"}
    assert by_title["Implementar autenticação JWT"]["days_overdue"] == 3
    assert by_title["Corrigir bug no filtro de busca"]["days_overdue"] == 1


def test_summary_user_productivity(admin_client):
    users = _users(admin_client)
    assert set(users) == {"João Silva", "Maria Santos", "Pedro Oliveira"}
    for u in users.values():
        assert set(u) == {"user_id", "user_name", "total_tasks", "completed_tasks", "completion_rate"}
    assert (users["João Silva"]["total_tasks"], users["João Silva"]["completed_tasks"],
            users["João Silva"]["completion_rate"]) == (4, 0, 0)
    assert (users["Maria Santos"]["total_tasks"], users["Maria Santos"]["completed_tasks"]) == (3, 0)
    assert (users["Pedro Oliveira"]["total_tasks"], users["Pedro Oliveira"]["completed_tasks"],
            users["Pedro Oliveira"]["completion_rate"]) == (3, 1, 33.33)


def test_user_report_joao(admin_client):
    uid = _users(admin_client)["João Silva"]["user_id"]
    r = admin_client.get(f"/reports/user/{uid}")
    assert r.status_code == 200
    b = r.get_json()
    assert b["user"] == {"id": uid, "name": "João Silva", "email": "joao@email.com"}
    assert b["statistics"] == {"total_tasks": 4, "done": 0, "pending": 4, "in_progress": 0,
                               "cancelled": 0, "overdue": 2, "high_priority": 2,
                               "completion_rate": 0}


def test_user_report_pedro(admin_client):
    uid = _users(admin_client)["Pedro Oliveira"]["user_id"]
    st = admin_client.get(f"/reports/user/{uid}").get_json()["statistics"]
    assert st == {"total_tasks": 3, "done": 1, "pending": 1, "in_progress": 0, "cancelled": 1,
                  "overdue": 0, "high_priority": 1, "completion_rate": 33.33}


def test_user_report_maria(admin_client):
    uid = _users(admin_client)["Maria Santos"]["user_id"]
    st = admin_client.get(f"/reports/user/{uid}").get_json()["statistics"]
    assert st["total_tasks"] == 3 and st["in_progress"] == 2 and st["pending"] == 1
    assert st["high_priority"] == 2 and st["overdue"] == 0


def test_user_report_404(admin_client):
    r = admin_client.get("/reports/user/9999")
    assert r.status_code == 404
    assert r.get_json() == {"error": "Usuário não encontrado"}


def test_criar_task_sobe_total(admin_client):
    uid = _users(admin_client)["Maria Santos"]["user_id"]
    r = admin_client.post("/tasks", json={"title": "Nova task de teste", "user_id": uid})
    assert r.status_code in (200, 201)
    s = admin_client.get("/reports/summary").get_json()
    assert s["overview"]["total_tasks"] == 11
    assert s["tasks_by_status"]["pending"] == 7
    assert admin_client.get(f"/reports/user/{uid}").get_json()["statistics"]["total_tasks"] == 4


def test_marcar_done_altera_completion_rate(admin_client):
    uid = _users(admin_client)["João Silva"]["user_id"]
    tasks = admin_client.get("/tasks").get_json()
    tid = next(t["id"] for t in tasks if t["title"] == "Adicionar paginação na API")
    r = admin_client.put(f"/tasks/{tid}", json={"status": "done"})
    assert r.status_code == 200
    st = admin_client.get(f"/reports/user/{uid}").get_json()["statistics"]
    assert st["done"] == 1
    assert st["completion_rate"] == round(1 / 4 * 100, 2)
    s = admin_client.get("/reports/summary").get_json()
    assert s["tasks_by_status"]["done"] == 2
    assert s["recent_activity"]["tasks_completed_last_7_days"] == 2


# ---------------------------------------------------------------- new_behavior

@pytest.mark.new_behavior
def test_summary_admin_desligado_403(client):
    r = client.get("/reports/summary")
    assert r.status_code == 403
    assert r.get_json() == {"error": "Recurso desabilitado"}


@pytest.mark.new_behavior
def test_summary_sem_token_401(flags_client):
    r = flags_client.get("/reports/summary")
    assert r.status_code == 401
    assert r.get_json() == {"error": "Não autorizado"}


@pytest.mark.new_behavior
def test_summary_token_errado_401(wrong_token_client):
    assert wrong_token_client.get("/reports/summary").status_code == 401


@pytest.mark.new_behavior
def test_user_report_admin_desligado_403(client):
    r = client.get("/reports/user/1")
    assert r.status_code == 403
    assert r.get_json() == {"error": "Recurso desabilitado"}


@pytest.mark.new_behavior
def test_user_report_sem_token_401(flags_client):
    r = flags_client.get("/reports/user/1")
    assert r.status_code == 401
    assert r.get_json() == {"error": "Não autorizado"}


@pytest.mark.new_behavior
def test_secret_key_nao_hardcoded(app):
    assert app.config["SECRET_KEY"] != "super-secret-key-123"


def _py_files():
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in ("tests", ".venv", "__pycache__", ".git")]
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(root, f)


@pytest.mark.new_behavior
@pytest.mark.parametrize("literal", ["super-secret-key-123", "senha123"])
def test_sem_segredos_literais_no_codigo(literal):
    hits = []
    for path in _py_files():
        with open(path, encoding="utf-8", errors="ignore") as fh:
            if literal in fh.read():
                hits.append(os.path.relpath(path, PROJECT_ROOT))
    assert hits == []


@pytest.mark.new_behavior
def test_settings_debug_false_por_padrao(monkeypatch):
    monkeypatch.delenv("DEBUG", raising=False)
    sys.modules.pop("config.settings", None)
    settings = importlib.import_module("config.settings")
    settings = importlib.reload(settings)
    assert settings.DEBUG is False


@pytest.mark.new_behavior
def test_cors_nao_aberto_para_qualquer_origem(client):
    r = client.get("/", headers={"Origin": "http://evil.example"})
    acao = r.headers.get("Access-Control-Allow-Origin")
    assert acao not in ("*", "http://evil.example")
