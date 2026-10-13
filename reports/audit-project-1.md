# Architecture Audit Report: code-smells-project

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3.13 + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
```

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 4 | LOW: 2

## Findings

### [CRITICAL] Hardcoded Credentials (AP-01)
File: app.py:7, controllers.py:289
Description: A `SECRET_KEY` do Flask é um literal no código (`"minha-chave-super-secreta-123"`) e o mesmo valor é repetido como literal na resposta do `GET /health`.
Impact: Qualquer pessoa com acesso ao repositório ou à rota `/health` obtém a chave usada para assinar sessões e cookies.
Recommendation: T01 — ler a chave de variável de ambiente num módulo de config (com default só para desenvolvimento) e removê-la da resposta do health check.

### [CRITICAL] Unauthenticated Destructive and Sensitive Endpoints (AP-07)
File: app.py:18, app.py:19, app.py:28, app.py:47-57, app.py:59-78
Description: `POST /admin/reset-db` apaga todas as tabelas e `POST /admin/query` executa qualquer SQL recebido no corpo, ambos sem nenhuma verificação de identidade; `GET /usuarios`, `GET /usuarios/<id>` (dados pessoais e senhas) e `GET /relatorios/vendas` (faturamento) também são públicos.
Impact: Qualquer cliente da rede apaga o banco, lê ou altera qualquer tabela e extrai dados pessoais e financeiros.
Recommendation: T08 — proteger as rotas administrativas com uma flag/credencial de config (desligada por padrão, 403) e exigir identidade nas rotas de dados sensíveis.

### [CRITICAL] SQL Injection (AP-02)
File: app.py:69, models.py:47-50, models.py:57-61, models.py:109-111, models.py:126-129, models.py:140, models.py:148-151, models.py:155, models.py:157-161, models.py:163-166, models.py:291, models.py:293
Description: As consultas são montadas por concatenação de strings com valores vindos do cliente: corpo de `POST/PUT /produtos` (nome, descrição, categoria, preço, estoque), `POST /login` (email e senha — permite login com `' OR '1'='1`), `POST /usuarios`, `POST /pedidos` (`usuario_id`, `produto_id`, `quantidade` sem conversão de tipo) e query string de `GET /produtos/busca` (`q`, `categoria`); `POST /admin/query` executa SQL arbitrário. As concatenações em models.py:28, 68, 92, 174, 280 usam parâmetro de caminho com conversor `<int:>` (ou status validado por lista) e as de models.py:188, 192, 220, 224 usam valores do próprio banco: má prática, mas não exploráveis.
Impact: Um atacante contorna o login, lê a tabela de usuários com senhas ou altera/apaga dados.
Recommendation: T02 — trocar toda concatenação por consultas parametrizadas (`?`) e remover o endpoint de SQL livre (ou deixá-lo atrás da flag de admin do T08).

### [CRITICAL] Sensitive Data Exposure and Plaintext Passwords (AP-04)
File: controllers.py:285-289, database.py:76-78, models.py:75-86, models.py:92-102, models.py:110, models.py:126-128
Description: As senhas são gravadas e comparadas em texto puro; `get_todos_usuarios` e `get_usuario_por_id` fazem `SELECT *` e devolvem o campo `senha` nas rotas `GET /usuarios` e `GET /usuarios/<id>`; o `GET /health` devolve `secret_key`, `debug` e `db_path`.
Impact: Quem chama a API ou lê o banco obtém as senhas de todos os usuários e a chave da aplicação.
Recommendation: T04 (hash forte com salt, refazendo o seed com as mesmas senhas de exemplo) e T05 (serialização explícita sem `senha` e health check sem dados de configuração).

### [HIGH] Insecure Configuration (AP-15)
File: app.py:8, app.py:9, app.py:88
Description: `DEBUG = True` e `app.run(host="0.0.0.0", debug=True)` estão fixos no código, sem depender do ambiente, e `CORS(app)` libera qualquer origem para todas as rotas, inclusive as que alteram dados.
Impact: O depurador do Werkzeug exposto na rede permite execução de código, e qualquer site pode disparar escritas na API pelo navegador da vítima.
Recommendation: T18 — ler debug, host e origens de CORS do módulo de config, com debug desligado por padrão.

### [HIGH] Unauthenticated Write Endpoints and Fake Login (AP-07)
File: app.py:14, app.py:15, app.py:16, app.py:21, app.py:26
Description: Criar, alterar e excluir produtos e mudar o status de pedidos não exigem identidade; o `POST /login` só devolve os dados do usuário, sem token ou sessão que outra rota verifique.
Impact: Qualquer cliente altera o catálogo e o status de pedidos; o login não protege nada.
Recommendation: T08 — introduzir verificação de identidade/papel nas rotas de escrita administrativa (mantendo o contrato atual atrás de flag de config durante a migração).

### [HIGH] Business Rules and Data Access in the Wrong Layer (AP-05)
File: app.py:49-55, app.py:66-76, controllers.py:247-250, controllers.py:264-274, models.py:139-146, models.py:256-262
Description: Rotas em `app.py` e o `health_check` acessam o banco direto; o cálculo de desconto por faixa de faturamento e a validação de estoque/total do pedido ficam no módulo de dados; a decisão de status do pedido fica no controller e o cancelamento só imprime "Devolver estoque", sem devolver.
Impact: A regra não pode ser testada sem banco e HTTP, e o cancelamento deixa o estoque inconsistente.
Recommendation: T06 — mover regras de pedido, estoque e relatório para uma camada de serviço e deixar models só com acesso a dados.

### [HIGH] Global Mutable Database Connection (AP-06)
File: database.py:4-10
Description: `get_db()` reatribui a global `db_connection` e compartilha uma única conexão SQLite (`check_same_thread=False`) entre todas as requisições e threads, sem rollback.
Impact: Requisições concorrentes compartilham transação: um erro no meio de um pedido deixa escritas parciais que a próxima requisição comita.
Recommendation: T07 — conexão por requisição (via `flask.g` + `teardown_appcontext`), com commit/rollback explícitos.

### [MEDIUM] Missing Input Validation (AP-14)
File: app.py:61-62, controllers.py:43-50, controllers.py:118-121, controllers.py:169-171, controllers.py:195-201, controllers.py:239-240, models.py:144-146
Description: Corpo ausente em `/admin/query`, `/login` e `/pedidos/<id>/status` gera `AttributeError` (500 em vez de 400); `preco`/`estoque` não têm tipo checado (string → 500); `preco_min`/`preco_max` inválidos geram 500; os itens do pedido não são validados, e quantidade negativa ou zero é aceita, reduzindo o total e aumentando o estoque.
Impact: Entradas malformadas viram 500 e quantidades negativas corrompem total e estoque.
Recommendation: T17 — validar presença, tipo e faixa na borda e devolver 400 com mensagem clara.

### [MEDIUM] Generic Error Handling Leaking Internals (AP-09)
File: app.py:77-78, controllers.py:10-12, controllers.py:21-22, controllers.py:60-62, controllers.py:95-96, controllers.py:108-109, controllers.py:125-126, controllers.py:133-134, controllers.py:143-144, controllers.py:164-165, controllers.py:185-186, controllers.py:218-220, controllers.py:226-227, controllers.py:234-235, controllers.py:254-255, controllers.py:261-262, controllers.py:291-292
Description: Todo handler captura `Exception` genérica e devolve `str(e)` ao cliente com status 500; não existe handler central nem distinção entre erro de validação e falha real.
Impact: Mensagens internas (SQL, nomes de tabela) vazam e erros do cliente aparecem como 500.
Recommendation: T10 — handler de erro central com exceções de domínio mapeadas para status, logando o detalhe e devolvendo mensagem genérica no 500.

### [MEDIUM] Duplicated Logic (AP-13)
File: controllers.py:28-54, controllers.py:72-90, models.py:12-21, models.py:31-40, models.py:177-200, models.py:210-232, models.py:304-313
Description: A validação de produto está copiada em `criar_produto` e `atualizar_produto` e já diverge (a atualização não valida tamanho do nome nem categoria); a serialização de produto aparece três vezes e a montagem de pedidos com itens duas vezes.
Impact: Correções aplicadas em uma cópia não chegam à outra, como já ocorreu na validação de atualização.
Recommendation: T16 — validador único de produto e funções de serialização compartilhadas.

### [MEDIUM] N+1 Queries (AP-08)
File: models.py:139-141, models.py:154-156, models.py:187-193, models.py:219-225
Description: `get_pedidos_usuario` e `get_todos_pedidos` fazem uma consulta de itens por pedido e uma consulta de produto por item; `criar_pedido` consulta cada produto duas vezes (validação e inserção).
Impact: O número de consultas cresce com pedidos × itens, degradando `GET /pedidos` conforme a base cresce.
Recommendation: T09 — carregar itens com `JOIN` em `produtos` numa única consulta (ou `IN`) e reaproveitar os produtos já lidos em `criar_pedido`.

### [LOW] Print as Logging, Dead Code and Poor Naming (AP-12)
File: app.py:56, app.py:83-86, controllers.py:8, controllers.py:11, controllers.py:57, controllers.py:61, controllers.py:106, controllers.py:161, controllers.py:179, controllers.py:182, controllers.py:208-210, controllers.py:219, controllers.py:248, controllers.py:250, controllers.py:267-268, database.py:2, models.py:2
Description: `print` é usado como log e como notificação simulada (e-mail, SMS, push), inclusive com e-mail do usuário; `import os` (database.py) e `import sqlite3` (models.py) não são usados; o `SELECT 1` do health check é descartado; parâmetros chamados `id` sombreiam o builtin.
Impact: Sem níveis nem destino de log, e notificações fingidas confundem quem lê o código.
Recommendation: T13 (logger sem dado sensível), T14 (remover imports e consulta mortos) e T15 (nomes claros).

### [LOW] Magic Numbers and Strings (AP-11)
File: controllers.py:47-49, controllers.py:52, controllers.py:242, models.py:150, models.py:247-253, models.py:257-262
Description: Faixas e taxas de desconto (10000/5000/1000, 0.1/0.05/0.02), limites de nome (2/200), lista de categorias e de status estão como literais espalhados.
Impact: Mudar uma regra exige caçar literais e pode deixar cópias inconsistentes.
Recommendation: T12 — constantes nomeadas num módulo de domínio/config.

```
================================
Total: 14 findings
================================
```
