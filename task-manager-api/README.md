# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. O código foi refatorado para MVC pela skill: rotas só registram, controllers adaptam HTTP, services concentram a regra de negócio e models fazem o acesso a dados.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # opcional; ajuste os valores
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000` (porta configurável por `PORT`; no macOS a 5000 costuma estar ocupada pelo AirPlay, use `PORT=5001 python app.py`). O `seed.py` apaga e repopula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo. **Rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias. Logins de exemplo: `joao@email.com` / `1234` (admin), `maria@email.com` / `abcd`, `pedro@email.com` / `pass`.

## Estrutura

```
app.py            entry point: cria o app, registra CORS, banco, rotas e o handler de erro
config/           settings.py (ambiente / .env) e rules.py (constantes de domínio)
database.py       instância do SQLAlchemy e commit/rollback
models/           entidades e consultas (task, user, category)
services/         regra de negócio, erros de domínio e persistência
controllers/      leem a requisição, chamam o service e montam a resposta
routes/           só mapeiam método + caminho para o controller
serializers/      campos públicos de cada entidade (o hash da senha nunca sai)
middlewares/      handler central de erros e guard administrativo
utils/            hash de senha e relógio UTC
```

## Configuração

Todas as variáveis estão em `.env.example`. As principais:

| Variável | Default | Observação |
| --- | --- | --- |
| `SECRET_KEY` | aleatória em dev | Obrigatória com `APP_ENV=production` (o boot falha sem ela) |
| `PORT` / `HOST` | `5000` / `0.0.0.0` | Mesmos valores do original |
| `DEBUG` | `false` | O debugger do Werkzeug não deve ficar ligado fora da máquina local |
| `CORS_ORIGINS` | `*` em dev; nenhuma em produção | Lista separada por vírgula |
| `ENABLE_ADMIN_ROUTES` / `ADMIN_TOKEN` | `false` / vazio | Ver abaixo |

## Rotas protegidas

A API ainda não tem autenticação real: o `token` devolvido por `POST /login` (`fake-jwt-token-<id>`) não é verificado por nenhuma rota. Até existir autenticação, as rotas destrutivas e de relatório continuam registradas, mas respondem **403** por padrão:

- `DELETE /tasks/<id>`, `DELETE /users/<id>`, `DELETE /categories/<id>`
- `GET /reports/summary`, `GET /reports/user/<id>`

Com `ENABLE_ADMIN_ROUTES=true`, elas exigem o cabeçalho `X-Admin-Token` igual a `ADMIN_TOKEN` (401 sem ele). O mesmo token é exigido para criar usuário com `role` diferente de `user` ou trocar o `role` de um usuário (403 sem ele).

```bash
ENABLE_ADMIN_ROUTES=true ADMIN_TOKEN=troque-me python app.py
curl -X DELETE -H 'X-Admin-Token: troque-me' localhost:5000/tasks/1
```

**Credenciais que estavam no código** (`SECRET_KEY` e a senha SMTP do antigo `NotificationService`) foram removidas, mas continuam no histórico do git: precisam ser rotacionadas.
