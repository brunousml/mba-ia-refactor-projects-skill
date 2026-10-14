# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000` (mude com `PORT`; no macOS a 5000 costuma estar ocupada pelo AirPlay). O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo. As senhas são gravadas com hash scrypt; um `loja.db` antigo, com senhas em texto, é convertido no boot.

A configuração vem de variáveis de ambiente. Veja `.env.example`. Em `APP_ENV=production`, `SECRET_KEY` é obrigatória.

## Estrutura

```
app.py          entry point: carrega config, cria o banco, registra middlewares e rotas
config/         settings (ambiente) e regras (constantes de domínio)
routes/         método + caminho -> controller
controllers/    lê a requisição, chama o serviço, monta a resposta
services/       regra de negócio e erros de domínio
models/         SQL parametrizado, schema e seed
serializers/    campos públicos de cada entidade (sem senha)
middlewares/    conexão por requisição, erro central, guard de admin
utils/          hash de senha e checagem de tipos
```

## Rotas de administração

`POST /admin/reset-db` e `POST /admin/query` continuam registradas, mas respondem **403** por padrão. Para usá-las, defina `ENABLE_ADMIN_ROUTES=true` e `ADMIN_TOKEN`, e envie o token no header `X-Admin-Token` (sem ele: 401). Decisão: são operações destrutivas e de SQL livre, que não podem ficar abertas sem autenticação.
