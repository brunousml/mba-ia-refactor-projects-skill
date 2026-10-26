"""Testes do domínio USERS + LOGIN (escritos antes da refatoração).

Caracterização: passa no original. new_behavior: especifica o refatorado.
"""
import hashlib

import pytest

USER_KEYS = {"id", "name", "email", "role", "active", "created_at"}
DENIED = {"error": "Recurso desabilitado"}
UNAUTH = {"error": "Não autorizado"}


def _md5(s):
    return hashlib.md5(s.encode()).hexdigest()


def _new_user(**over):
    data = {"name": "Ana", "email": "ana@email.com", "password": "senha123"}
    data.update(over)
    return data


# ---------------------------------------------------------------- GET /users
def test_list_users(admin_client):
    r = admin_client.get("/users")
    assert r.status_code == 200
    body = r.get_json()
    assert len(body) == 3
    for u in body:
        assert USER_KEYS | {"task_count"} <= set(u)
    counts = {u["email"]: u["task_count"] for u in body}
    assert counts == {"joao@email.com": 4, "maria@email.com": 3, "pedro@email.com": 3}
    roles = {u["email"]: u["role"] for u in body}
    assert roles == {"joao@email.com": "admin", "maria@email.com": "user", "pedro@email.com": "manager"}


# ------------------------------------------------------------ GET /users/<id>
def test_get_user(admin_client):
    r = admin_client.get("/users/1")
    assert r.status_code == 200
    body = r.get_json()
    assert USER_KEYS <= set(body)
    assert body["email"] == "joao@email.com"
    assert isinstance(body["tasks"], list) and len(body["tasks"]) == 4
    assert all(t["user_id"] == 1 for t in body["tasks"])


def test_get_user_not_found(admin_client):
    r = admin_client.get("/users/999")
    assert r.status_code == 404
    assert r.get_json() == {"error": "Usuário não encontrado"}


# --------------------------------------------------------------- POST /users
def test_create_user_default_role(admin_client):
    r = admin_client.post("/users", json=_new_user())
    assert r.status_code == 201
    body = r.get_json()
    assert USER_KEYS <= set(body)
    assert body["name"] == "Ana" and body["email"] == "ana@email.com"
    assert body["role"] == "user" and body["active"] is True
    assert admin_client.get("/users/%d" % body["id"]).status_code == 200


def test_create_user_with_role(admin_client):
    r = admin_client.post("/users", json=_new_user(role="manager"))
    assert r.status_code == 201
    assert r.get_json()["role"] == "manager"


@pytest.mark.parametrize("payload,msg", [
    ({"email": "a@b.com", "password": "1234"}, "Nome é obrigatório"),
    ({"name": "A", "password": "1234"}, "Email é obrigatório"),
    ({"name": "A", "email": "a@b.com"}, "Senha é obrigatória"),
    ({"name": "A", "email": "invalido", "password": "1234"}, "Email inválido"),
    ({"name": "A", "email": "a@b.com", "password": "123"}, "Senha deve ter no mínimo 4 caracteres"),
    ({"name": "A", "email": "a@b.com", "password": "1234", "role": "root"}, "Role inválido"),
])
def test_create_user_validation(admin_client, payload, msg):
    r = admin_client.post("/users", json=payload)
    assert r.status_code == 400
    assert r.get_json() == {"error": msg}


def test_create_user_empty_body(admin_client):
    r = admin_client.post("/users", json={})
    assert r.status_code == 400
    assert r.get_json() == {"error": "Dados inválidos"}


def test_create_user_duplicate_email(admin_client):
    r = admin_client.post("/users", json=_new_user(email="maria@email.com"))
    assert r.status_code == 409
    assert r.get_json() == {"error": "Email já cadastrado"}


# --------------------------------------------------------- PUT /users/<id>
def test_update_user(admin_client):
    r = admin_client.put("/users/2", json={"name": "Maria Nova", "role": "manager"})
    assert r.status_code == 200
    body = r.get_json()
    assert USER_KEYS <= set(body)
    assert body["name"] == "Maria Nova" and body["role"] == "manager"


def test_update_user_password_then_login(admin_client, client):
    r = admin_client.put("/users/2", json={"password": "novasenha"})
    assert r.status_code == 200
    assert client.post("/login", json={"email": "maria@email.com", "password": "novasenha"}).status_code == 200
    assert client.post("/login", json={"email": "maria@email.com", "password": "abcd"}).status_code == 401


def test_update_user_not_found(admin_client):
    r = admin_client.put("/users/999", json={"name": "X"})
    assert r.status_code == 404
    assert r.get_json() == {"error": "Usuário não encontrado"}


@pytest.mark.parametrize("payload,status,msg", [
    ({}, 400, "Dados inválidos"),
    ({"email": "invalido"}, 400, "Email inválido"),
    ({"email": "joao@email.com"}, 409, "Email já cadastrado"),
    ({"password": "12"}, 400, "Senha muito curta"),
    ({"role": "root"}, 400, "Role inválido"),
])
def test_update_user_validation(admin_client, payload, status, msg):
    r = admin_client.put("/users/2", json=payload)
    assert r.status_code == status
    assert r.get_json() == {"error": msg}


def test_update_user_same_email_ok(admin_client):
    r = admin_client.put("/users/2", json={"email": "maria@email.com"})
    assert r.status_code == 200


# ------------------------------------------------------ DELETE /users/<id>
def test_delete_user_removes_tasks(admin_client):
    task_ids = [t["id"] for t in admin_client.get("/users/1").get_json()["tasks"]]
    assert len(task_ids) == 4
    r = admin_client.delete("/users/1")
    assert r.status_code == 200
    assert r.get_json() == {"message": "Usuário deletado com sucesso"}
    assert admin_client.get("/users/1").status_code == 404
    for tid in task_ids:
        assert admin_client.get("/tasks/%d" % tid).status_code == 404


def test_delete_user_not_found(admin_client):
    r = admin_client.delete("/users/999")
    assert r.status_code == 404
    assert r.get_json() == {"error": "Usuário não encontrado"}


# ---------------------------------------------------- GET /users/<id>/tasks
def test_user_tasks_public(client):
    r = client.get("/users/1/tasks")
    assert r.status_code == 200
    body = r.get_json()
    assert len(body) == 4
    keys = {"id", "title", "description", "status", "priority", "created_at", "due_date", "overdue"}
    for t in body:
        assert keys <= set(t)
    overdue = {t["title"]: t["overdue"] for t in body}
    assert overdue["Implementar autenticação JWT"] is True
    assert overdue["Adicionar paginação na API"] is False
    assert overdue["Melhorar validações de input"] is False


def test_user_tasks_not_found(client):
    r = client.get("/users/999/tasks")
    assert r.status_code == 404
    assert r.get_json() == {"error": "Usuário não encontrado"}


# --------------------------------------------------------------- POST /login
@pytest.mark.parametrize("uid,email,pwd", [
    (1, "joao@email.com", "1234"),
    (2, "maria@email.com", "abcd"),
    (3, "pedro@email.com", "pass"),
])
def test_login_seed_users(client, uid, email, pwd):
    r = client.post("/login", json={"email": email, "password": pwd})
    assert r.status_code == 200
    body = r.get_json()
    assert {"message", "user", "token"} <= set(body)
    assert body["token"] == "fake-jwt-token-%d" % uid
    assert USER_KEYS <= set(body["user"])
    assert body["user"]["id"] == uid


def test_login_new_user(admin_client, client):
    uid = admin_client.post("/users", json=_new_user()).get_json()["id"]
    r = client.post("/login", json={"email": "ana@email.com", "password": "senha123"})
    assert r.status_code == 200
    assert r.get_json()["token"] == "fake-jwt-token-%d" % uid


@pytest.mark.parametrize("payload,status,msg", [
    ({}, 400, "Dados inválidos"),
    ({"email": "joao@email.com"}, 400, "Email e senha são obrigatórios"),
    ({"password": "1234"}, 400, "Email e senha são obrigatórios"),
    ({"email": "naoexiste@email.com", "password": "1234"}, 401, "Credenciais inválidas"),
    ({"email": "joao@email.com", "password": "errada"}, 401, "Credenciais inválidas"),
])
def test_login_errors(client, payload, status, msg):
    r = client.post("/login", json=payload)
    assert r.status_code == status
    assert r.get_json() == {"error": msg}


def test_login_inactive_user(admin_client, client):
    assert admin_client.put("/users/2", json={"active": False}).status_code == 200
    r = client.post("/login", json={"email": "maria@email.com", "password": "abcd"})
    assert r.status_code == 403
    assert r.get_json() == {"error": "Usuário inativo"}


# ============================================================ NEW BEHAVIOR
# T05: password nunca sai na resposta
@pytest.mark.new_behavior
def test_t05_get_user_hides_password(admin_client):
    assert "password" not in admin_client.get("/users/1").get_json()


@pytest.mark.new_behavior
def test_t05_create_user_hides_password(admin_client):
    r = admin_client.post("/users", json=_new_user())
    assert r.status_code == 201
    assert "password" not in r.get_json()


@pytest.mark.new_behavior
def test_t05_update_user_hides_password(admin_client):
    r = admin_client.put("/users/2", json={"name": "M"})
    assert r.status_code == 200
    assert "password" not in r.get_json()


@pytest.mark.new_behavior
def test_t05_login_hides_password(client):
    r = client.post("/login", json={"email": "joao@email.com", "password": "1234"})
    assert r.status_code == 200
    assert "password" not in r.get_json()["user"]


# T04: hash forte (não texto puro, não md5)
@pytest.mark.new_behavior
def test_t04_new_user_password_not_md5(admin_client, db_session):
    from models.user import User
    assert admin_client.post("/users", json=_new_user()).status_code == 201
    stored = db_session.query(User).filter_by(email="ana@email.com").first().password
    assert stored != "senha123"
    assert stored != _md5("senha123")


@pytest.mark.new_behavior
def test_t04_seed_password_not_md5(db_session):
    from models.user import User
    stored = db_session.query(User).filter_by(email="joao@email.com").first().password
    assert stored != "1234"
    assert stored != _md5("1234")


# T08 leitura sensível
@pytest.mark.new_behavior
@pytest.mark.parametrize("path", ["/users", "/users/1"])
def test_t08_sensitive_read_disabled(client, path):
    r = client.get(path)
    assert r.status_code == 403
    assert r.get_json() == DENIED


@pytest.mark.new_behavior
@pytest.mark.parametrize("path", ["/users", "/users/1"])
def test_t08_sensitive_read_no_token(flags_client, path):
    r = flags_client.get(path)
    assert r.status_code == 401
    assert r.get_json() == UNAUTH


@pytest.mark.new_behavior
@pytest.mark.parametrize("path", ["/users", "/users/1"])
def test_t08_sensitive_read_wrong_token(wrong_token_client, path):
    r = wrong_token_client.get(path)
    assert r.status_code == 401
    assert r.get_json() == UNAUTH


# T08 escrita
@pytest.mark.new_behavior
def test_t08_create_user_disabled(client, db_session):
    from models.user import User
    r = client.post("/users", json=_new_user())
    assert r.status_code == 403
    assert r.get_json() == DENIED
    assert db_session.query(User).filter_by(email="ana@email.com").first() is None


@pytest.mark.new_behavior
def test_t08_create_user_no_token(flags_client):
    r = flags_client.post("/users", json=_new_user())
    assert r.status_code == 401
    assert r.get_json() == UNAUTH


@pytest.mark.new_behavior
def test_t08_create_user_wrong_token(wrong_token_client):
    r = wrong_token_client.post("/users", json=_new_user())
    assert r.status_code == 401
    assert r.get_json() == UNAUTH


@pytest.mark.new_behavior
def test_ap15_create_admin_blocked(client, db_session):
    from models.user import User
    r = client.post("/users", json=_new_user(role="admin"))
    assert r.status_code == 403
    assert db_session.query(User).count() == 3


@pytest.mark.new_behavior
def test_t08_update_user_disabled(client):
    r = client.put("/users/2", json={"role": "admin"})
    assert r.status_code == 403
    assert r.get_json() == DENIED


@pytest.mark.new_behavior
def test_t08_update_user_no_token(flags_client):
    r = flags_client.put("/users/2", json={"role": "admin"})
    assert r.status_code == 401
    assert r.get_json() == UNAUTH


@pytest.mark.new_behavior
def test_t08_update_user_wrong_token(wrong_token_client):
    r = wrong_token_client.put("/users/2", json={"role": "admin"})
    assert r.status_code == 401
    assert r.get_json() == UNAUTH


# T08 admin
@pytest.mark.new_behavior
def test_t08_delete_user_disabled(client, db_session):
    from models.user import User
    r = client.delete("/users/2")
    assert r.status_code == 403
    assert r.get_json() == DENIED
    assert db_session.get(User, 2) is not None


@pytest.mark.new_behavior
def test_t08_delete_user_no_token(flags_client, db_session):
    from models.user import User
    r = flags_client.delete("/users/2")
    assert r.status_code == 401
    assert r.get_json() == UNAUTH
    assert db_session.get(User, 2) is not None


# T17 checagem de tipo
@pytest.mark.new_behavior
def test_t17_create_user_int_password(admin_client):
    r = admin_client.post("/users", json=_new_user(password=12345))
    assert r.status_code == 400
    assert "error" in r.get_json()


@pytest.mark.new_behavior
def test_t17_update_user_int_password(admin_client):
    r = admin_client.put("/users/2", json={"password": 1234})
    assert r.status_code == 400
    assert "error" in r.get_json()


@pytest.mark.new_behavior
def test_t17_update_user_string_active(admin_client):
    r = admin_client.put("/users/2", json={"active": "sim"})
    assert r.status_code == 400
    assert "error" in r.get_json()


@pytest.mark.new_behavior
def test_t17_create_user_int_name(admin_client):
    r = admin_client.post("/users", json=_new_user(name=123))
    assert r.status_code == 400
    assert "error" in r.get_json()


@pytest.mark.new_behavior
def test_t08_delete_user_wrong_token(wrong_token_client, db_session):
    from models.user import User
    r = wrong_token_client.delete("/users/2")
    assert r.status_code == 401
    assert r.get_json() == UNAUTH
    db_session.expire_all()
    assert db_session.get(User, 2) is not None
