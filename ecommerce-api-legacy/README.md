# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express, refatorada para MVC pela skill `refactor-arch`.

## Como rodar

```bash
npm install
npm start      # http://localhost:3000 (PORT muda a porta)
npm test       # node:test: caracterização HTTP, comportamento novo e unitários
```

O banco SQLite é em memória (`DATABASE_FILE`) e recebe o seed no boot. A senha do usuário de exemplo `leonan@fullcycle.com.br` continua sendo `123`, agora armazenada com scrypt.

## Configuração

Veja `.env.example`. Nenhum segredo fica no código; a chave `pk_live_...` que estava no repositório precisa ser rotacionada.

## Rotas protegidas (T08)

As rotas existentes não tinham autenticação. Elas continuam registradas, mas ficam atrás de flags (default `false`, que responde **403**). Com a flag ligada, a rota exige o header `X-Admin-Token` igual a `ADMIN_TOKEN` (sem ele, **401**).

| Rota | Flag |
|---|---|
| `POST /api/checkout` | `ENABLE_WRITE_ROUTES` |
| `GET /api/admin/financial-report` | `ENABLE_ADMIN_ROUTES` |
| `DELETE /api/users/:id` | `ENABLE_ADMIN_ROUTES` |

## Estrutura

```
src/
  app.js          entry point: compõe dependências, middlewares e rotas
  config/         settings (ambiente) e rules (constantes de negócio)
  models/         conexão, schema/seed e consultas parametrizadas
  services/       checkout, relatório financeiro, usuários
  controllers/    validação de entrada e resposta HTTP
  routes/         método + caminho -> guard -> controller
  middlewares/    guards, asyncHandler, handler central de erro
  errors/         DomainError
  utils/          hash de senha e logger
```

Exemplos de requisições estão em `api.http`.
