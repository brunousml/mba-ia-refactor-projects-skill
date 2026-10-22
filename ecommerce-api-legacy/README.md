# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`, já refatorada para MVC.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000` (`PORT` muda a porta). O banco SQLite é em memória e carrega o seed no boot. As variáveis estão em `.env.example`.

## Estrutura

```
src/
  app.js          entry point: cria o banco, roda schema/seed, registra rotas e o handler de erro
  config/         settings (ambiente) e rules (constantes de negócio)
  models/         acesso a dados (adaptador sqlite com Promises, schema/seed, consultas)
  services/       checkout, pagamento, relatório, usuários
  controllers/    validação da entrada e montagem da resposta
  routes/         só registro de método + caminho
  middlewares/    guards por flag, asyncHandler, errorHandler
```

## Rotas protegidas por flag

Todas as rotas da API alteram dados ou expõem dados financeiros, e nenhuma tem autenticação real. Elas continuam registradas, mas ficam atrás de flags (default `false` → **403**). Com a flag ligada, exigem o header `X-Admin-Token` igual a `ADMIN_TOKEN` (sem ele, **401**).

| Rota | Flag |
| --- | --- |
| `POST /api/checkout` | `ENABLE_WRITE_ROUTES` |
| `GET /api/admin/financial-report` | `ENABLE_ADMIN_ROUTES` |
| `DELETE /api/users/:id` | `ENABLE_ADMIN_ROUTES` |

```bash
ENABLE_WRITE_ROUTES=true ENABLE_ADMIN_ROUTES=true ADMIN_TOKEN=meu-token npm start
```

Exemplos de requisições estão em `api.http`.

> A senha do banco e a chave `pk_live_...` que estavam no código precisam ser rotacionadas: removê-las do código não invalida a cópia que ficou no histórico do git.
