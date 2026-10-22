# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`, refatorada para MVC.

## Como rodar

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # opcional; as variáveis são lidas do ambiente
python app.py
```

A aplicação sobe em `http://localhost:5000` (`PORT` muda a porta; no macOS a 5000 costuma estar ocupada pelo AirPlay). O banco SQLite (`loja.db`, ou `DB_PATH`) é criado no boot, já com produtos e usuários de exemplo. As senhas do seed são gravadas com hash (scrypt); bancos antigos com senha em texto puro são migrados no boot.

## Estrutura

```
app.py          entry point: create_app() compõe config, banco, middlewares e rotas
config/         settings (ambiente) e regras de negócio nomeadas
models/         acesso a dados (SQL parametrizado), schema e seed
services/       regra de negócio e erros de domínio
controllers/    leitura da requisição, chamada ao serviço, resposta
routes/         mapeamento método + caminho -> controller, com guards
middlewares/    guards (T08), conexão por requisição, erro central
serializers/    campos públicos de cada entidade
utils/          hash de senha e checagem de tipos
tests/          pytest: caracterização, comportamento novo e unitários
```

## Rotas protegidas (T08)

A API não tem autenticação de usuário. Para não deixar rotas destrutivas ou sensíveis abertas, elas continuam registradas, mas ficam atrás de flags desligadas por padrão (respondem **403**). Com a flag ligada, exigem o header `X-Admin-Token` igual a `ADMIN_TOKEN` (senão **401**).

| Flag | Rotas |
|---|---|
| `ENABLE_ADMIN_ROUTES` | `POST /admin/reset-db`, `POST /admin/query`, `GET /relatorios/vendas` |
| `ENABLE_SENSITIVE_READS` | `GET /usuarios`, `GET /usuarios/<id>`, `GET /pedidos`, `GET /pedidos/usuario/<id>` |
| `ENABLE_WRITE_ROUTES` | `POST/PUT/DELETE /produtos`, `POST /usuarios`, `POST /pedidos`, `PUT /pedidos/<id>/status` |

Públicas: `GET /`, `GET /health`, `GET /produtos`, `GET /produtos/busca`, `GET /produtos/<id>`, `POST /login`.

```bash
ENABLE_WRITE_ROUTES=true ADMIN_TOKEN=troque-me python app.py
curl -X POST localhost:5000/produtos -H 'X-Admin-Token: troque-me' -H 'Content-Type: application/json' \
  -d '{"nome":"Livro","preco":10,"estoque":1,"categoria":"livros"}'
```

## Testes

```bash
.venv/bin/python -m pytest -q tests
```

## Segurança

A `SECRET_KEY` antiga (`minha-chave-...`) esteve no repositório e era devolvida pelo `/health`: considere-a vazada e defina uma nova em `SECRET_KEY`.
