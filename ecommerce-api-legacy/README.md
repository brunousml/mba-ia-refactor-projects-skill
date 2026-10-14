# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000` (configurável por `PORT`). O banco SQLite é em memória e já carrega seeds automaticamente no boot. O usuário de exemplo `leonan@fullcycle.com.br` usa a senha `123` (guardada com hash scrypt).

As variáveis de ambiente estão em `.env.example`. Exemplos de requisições estão em `api.http`.

## Rotas administrativas

`GET /api/admin/financial-report` e `DELETE /api/users/:id` ficam registradas, mas desligadas por padrão (respondem 403). Para ligar:

```bash
ENABLE_ADMIN_ROUTES=true ADMIN_TOKEN=<token> npm start
```

e envie o header `X-Admin-Token: <token>`. Token ausente ou errado responde 401.

## Estrutura

```
src/
  app.js          entry point: compõe banco, models, services, controllers e rotas
  config/         settings (ambiente) e rules (constantes de domínio)
  models/         acesso a dados (SQLite), schema e seed
  services/       regra de negócio: checkout, pagamento, relatório, usuários
  controllers/    leitura e validação da requisição, escolha do status
  routes/         mapeamento método + caminho -> controller
  middlewares/    guard administrativo, wrapper async e erro central
  errors/         erro de domínio
  utils/          hash de senha e logger
```

## Segurança

As credenciais que estavam no código (`dbPass`, `paymentGatewayKey`) vazaram no histórico do repositório e precisam ser **rotacionadas**.
