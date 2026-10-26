# code-smells-project

API de e-commerce em Python/Flask, refatorada para MVC (camadas `models/`, `services/`, `controllers/`, `routes/`).

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env        # opcional: ajuste as variáveis
python app.py
```

A aplicação sobe em `http://localhost:5000` (`PORT`). O banco SQLite (`loja.db`, ou `DB_PATH`) é criado na subida, já com produtos e usuários de exemplo.

**Atenção:** o seed agora grava senhas em hash. Um `loja.db` criado pela versão antiga continua com senhas em texto puro; apague o arquivo antes de subir esta versão.

## Configuração

| Variável | Default | Efeito |
| --- | --- | --- |
| `SECRET_KEY` | aleatória em dev | Obrigatória em `APP_ENV=production` |
| `DEBUG` | `false` | Modo debug do Flask |
| `HOST` / `PORT` | `0.0.0.0` / `5000` | Endereço do servidor |
| `DB_PATH` | `loja.db` | Arquivo do SQLite |
| `CORS_ORIGINS` | vazio | Origens liberadas para CORS, separadas por vírgula |
| `ENABLE_ADMIN_ROUTES` | `false` | Libera administração |
| `ENABLE_SENSITIVE_READS` | `false` | Libera leitura sensível |
| `ENABLE_WRITE_ROUTES` | `false` | Libera escrita |
| `ADMIN_TOKEN` | vazio | Token exigido no header `X-Admin-Token` quando uma flag está ligada |

## Controle de acesso

As rotas sem autenticação real continuam registradas, mas protegidas por flag. Com a flag desligada, respondem **403**. Com a flag ligada e sem o token certo, **401**.

| Flag | Rotas |
| --- | --- |
| `ENABLE_ADMIN_ROUTES` | `POST /admin/reset-db`, `POST /admin/query`, `GET /relatorios/vendas` |
| `ENABLE_SENSITIVE_READS` | `GET /usuarios`, `GET /usuarios/<id>`, `GET /pedidos`, `GET /pedidos/usuario/<id>` |
| `ENABLE_WRITE_ROUTES` | `POST/PUT/DELETE /produtos`, `POST /usuarios`, `POST /pedidos`, `PUT /pedidos/<id>/status` |

Sem guard: `GET /`, `GET /health`, leituras do catálogo (`/produtos`) e `POST /login`.

`POST /pedidos` segue o contrato original: a conta vem do `usuario_id` do corpo, sem credencial do dono. A proteção é o guard de escrita (`ENABLE_WRITE_ROUTES` e `X-Admin-Token`).

## Testes

```bash
pip install -r requirements-dev.txt
python -m pytest -q tests
```

Cada teste roda com banco novo, num diretório temporário.
