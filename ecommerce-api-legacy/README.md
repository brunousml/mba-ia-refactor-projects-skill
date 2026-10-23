# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`, refatorada para MVC.

## Como rodar

```bash
npm install
cp .env.example .env   # opcional; as variáveis são lidas do ambiente
npm start
```

A aplicação sobe em `http://localhost:3000` (`PORT` muda a porta). O banco SQLite é em memória e carrega o seed no boot; a senha do usuário de exemplo (`leonan@fullcycle.com.br`) continua `123`, agora gravada com hash scrypt.

Exemplos de requisições estão em `api.http`.

## Acesso às rotas (guards por flag)

Nenhuma rota tinha autenticação. Elas continuam registradas, mas protegidas por flags desligadas por default:

| Rota | Flag |
|---|---|
| `POST /api/checkout` | `ENABLE_WRITE_ROUTES` |
| `GET /api/admin/financial-report` | `ENABLE_ADMIN_ROUTES` |
| `DELETE /api/users/:id` | `ENABLE_ADMIN_ROUTES` |

Flag desligada: **403**. Flag ligada: exige `X-Admin-Token` igual a `ADMIN_TOKEN` (**401** sem ele). Para o comportamento original:

```bash
ENABLE_WRITE_ROUTES=true ENABLE_ADMIN_ROUTES=true ADMIN_TOKEN=troque-me npm start
curl -H 'X-Admin-Token: troque-me' localhost:3000/api/admin/financial-report
```

As credenciais que estavam no código (senha do banco, chave `pk_live_` do gateway) foram removidas e **precisam ser rotacionadas**, porque continuam no histórico do repositório.

## Estrutura

```
src/
  app.js          entry point: compõe config, banco, middlewares e rotas
  config/         settings (ambiente) e rules (constantes de pagamento)
  models/         acesso a dados (SQLite com promises), schema e seed
  services/       regra de negócio: checkout, relatório, usuários
  controllers/    validação de entrada e montagem da resposta
  routes/         método + caminho -> guard + controller
  middlewares/    guards (T08), handler de erro central, asyncHandler
  errors/         DomainError
  utils/          hash de senha e logger
tests/            caracterização HTTP + unitários (node:test)
```

## Testes

```bash
npm test
```

A suíte sobe a aplicação como processo filho na porta 3000, então roda em série.
