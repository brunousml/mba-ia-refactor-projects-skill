"""Unitários das camadas novas (services/), sem HTTP, com o banco de teste."""
from datetime import timedelta

import pytest

pytestmark = pytest.mark.unit


@pytest.fixture
def ctx(app):
    with app.app_context():
        yield


def test_task_service_stats_do_seed(ctx):
    from services import task_service

    stats = task_service.stats()
    assert stats == {
        "total": 10, "pending": 6, "in_progress": 2, "done": 1,
        "cancelled": 1, "overdue": 2, "completion_rate": 10.0,
    }


def test_task_service_get_inexistente_lanca_not_found(ctx):
    from services import task_service
    from services.errors import NotFoundError

    with pytest.raises(NotFoundError) as exc:
        task_service.get_task(9999)
    assert exc.value.status == 404
    assert str(exc.value) == "Task não encontrada"


def test_task_service_create_valida_titulo(ctx):
    from services import task_service
    from services.errors import DomainError

    with pytest.raises(DomainError) as exc:
        task_service.create_task({"title": "ab"})
    assert exc.value.status == 400
    assert str(exc.value) == "Título muito curto"


def test_task_overdue_regra_unica():
    from models.task import Task

    from utils.time import utc_now
    passado = utc_now() - timedelta(days=1)
    assert Task(due_date=passado, status="pending").is_overdue() is True
    assert Task(due_date=passado, status="done").is_overdue() is False
    assert Task(due_date=None, status="pending").is_overdue() is False


def test_user_service_email_duplicado_lanca_conflito(ctx):
    from services import user_service
    from services.errors import DomainError

    with pytest.raises(DomainError) as exc:
        user_service.create_user({"name": "X", "email": "joao@email.com", "password": "abcdef"})
    assert exc.value.status == 409


def test_user_service_login_credenciais(ctx):
    from services import user_service
    from services.errors import DomainError

    user = user_service.login("maria@email.com", "abcd")
    assert user.email == "maria@email.com"
    with pytest.raises(DomainError) as exc:
        user_service.login("maria@email.com", "errada")
    assert exc.value.status == 401


def test_user_service_lista_com_contagem(ctx):
    from services import user_service

    contagens = {u.email: n for u, n in user_service.list_users()}
    assert contagens == {"joao@email.com": 4, "maria@email.com": 3, "pedro@email.com": 3}


def test_category_service_lista_com_contagem(ctx):
    from services import category_service

    contagens = {c.name: n for c, n in category_service.list_categories()}
    assert contagens == {"Backend": 6, "Frontend": 1, "DevOps": 2, "Bug": 1}


def test_report_service_summary(ctx):
    from services import report_service

    report = report_service.summary()
    assert report["overview"] == {"total_tasks": 10, "total_users": 3, "total_categories": 4}
    assert report["overdue"]["count"] == 2
    assert report["tasks_by_priority"]["critical"] == 2


def test_report_service_user_report_inexistente(ctx):
    from services import report_service
    from services.errors import NotFoundError

    with pytest.raises(NotFoundError):
        report_service.user_report(9999)
