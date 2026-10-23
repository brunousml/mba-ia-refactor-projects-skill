# task-manager-api

API de Task Manager em Python/Flask, organizada em MVC: `config/`, `models/` (acesso a dados), `services/` (regra de negócio), `controllers/` (HTTP), `routes/` (só registro), `middlewares/` (guards e erro central) e `serializers/` (campos públicos).

## Como rodar

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py
.venv/bin/python app.py
```

A aplicação sobe em `http://localhost:5000` (mude com `PORT`; no macOS a 5000 costuma estar ocupada pelo AirPlay). O `seed.py` recria o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo. As senhas de exemplo continuam `1234`, `abcd` e `pass`, agora gravadas com hash scrypt + salt.

Variáveis de ambiente: veja `.env.example`. Em `APP_ENV=production`, `SECRET_KEY` (e `ADMIN_TOKEN`, se alguma flag estiver ligada) são obrigatórios. `DEBUG` é desligado por default.

## Rotas protegidas

Não há autenticação real (o `/login` devolve um token que nenhuma rota verifica). Por isso as rotas sensíveis seguem registradas, mas atrás de flags, todas desligadas por default:

| Flag | Rotas |
|---|---|
| `ENABLE_ADMIN_ROUTES` | `DELETE /tasks/<id>`, `DELETE /users/<id>`, `DELETE /categories/<id>`, `GET /reports/summary`, `GET /reports/user/<id>` |
| `ENABLE_SENSITIVE_READS` | `GET /users`, `GET /users/<id>` |
| `ENABLE_WRITE_ROUTES` | `POST/PUT /tasks`, `POST/PUT /users`, `POST/PUT /categories` |

Flag desligada: **403**. Flag ligada: exige `X-Admin-Token` igual a `ADMIN_TOKEN`; sem ele ou com valor errado, **401**. Ficam públicas: `/`, `/health`, `/login`, `GET /tasks`, `GET /tasks/<id>`, `/tasks/search`, `/tasks/stats`, `GET /users/<id>/tasks` e `GET /categories`.

## Testes

```bash
.venv/bin/pip install pytest
.venv/bin/python -m pytest -q tests
```
