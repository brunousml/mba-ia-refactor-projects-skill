# Architecture Audit Report: code-smells-project

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
```

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 4 | LOW: 2

## Findings

### [CRITICAL] Hardcoded Credentials (AP-01)
File: app.py:7, controllers.py:289, database.py:76-78
Description: A `SECRET_KEY` do Flask é um literal no código e o mesmo valor é repetido no corpo do `/health`. O seed grava senhas reais de exemplo (`admin123`, `123456`, `senha123`) direto no código.
Impact: Quem lê o repositório ou chama `/health` obtém a chave de assinatura da aplicação.
Recommendation: T01 — ler `SECRET_KEY` de variável de ambiente num módulo de config e removê-la da resposta do health check.

### [CRITICAL] Unauthenticated Destructive and Sensitive Endpoints (AP-07)
File: app.py:16, app.py:18-19, app.py:24-25, app.py:28, app.py:30, app.py:47-57, app.py:59-78
Description: Nenhuma rota tem verificação de identidade. `POST /admin/reset-db` apaga todas as tabelas, `POST /admin/query` executa SQL arbitrário, `DELETE /produtos/<id>` apaga dados, `GET /usuarios` e `/usuarios/<id>` devolvem dados pessoais (com senha), `GET /pedidos` e `/pedidos/usuario/<id>` devolvem pedidos de qualquer cliente, `GET /relatorios/vendas` devolve dados financeiros e `GET /health` devolve a chave secreta.
Impact: Qualquer cliente anônimo apaga o banco, executa SQL ou lê dados pessoais e financeiros.
Recommendation: T08 — guard de administração (reset, query, relatório), de leitura sensível (usuários, pedidos) e de escrita (DELETE), controlados por flag e `X-Admin-Token`.

### [CRITICAL] SQL Injection (AP-02)
File: app.py:69, models.py:48-49, models.py:58-60, models.py:110, models.py:127-128, models.py:140, models.py:149-150, models.py:155, models.py:158-160, models.py:164-165, models.py:291, models.py:293
Description: As consultas são montadas por concatenação com valores do corpo (`nome`, `descricao`, `categoria`, `email`, `senha`, `usuario_id`, `produto_id`, `quantidade`) e da query string (`q`, `categoria`); `/admin/query` executa o SQL recebido. As concatenações em models.py:28, 68, 92, 174, 188, 192, 220, 224, 280, 295 e 297 recebem valores com conversor `int`/`float`, lista de valores permitidos ou do próprio banco: má prática, mas não exploráveis.
Impact: Bypass de login (`' OR '1'='1`), leitura e alteração arbitrária do banco.
Recommendation: T02 — consultas parametrizadas (`?`) em todo o model e remoção (ou guard) do executor de SQL.

### [CRITICAL] Sensitive Data Exposure and Plaintext Passwords (AP-04)
File: controllers.py:289, database.py:76-78, models.py:83, models.py:99, models.py:110, models.py:127-128
Description: Senhas são gravadas e comparadas em texto puro; `get_todos_usuarios` e `get_usuario_por_id` incluem o campo `senha`, devolvido por `GET /usuarios` e `GET /usuarios/<id>`; `/health` devolve `secret_key`.
Impact: Qualquer chamada à API ou leitura do banco revela todas as senhas.
Recommendation: T04 (hash com salt, refazendo o seed com as mesmas senhas de exemplo) e T05 (serialização sem `senha` e sem `secret_key`).

### [HIGH] Insecure Configuration (AP-15)
File: app.py:8, app.py:9, app.py:88
Description: `DEBUG = True` e `app.run(debug=True)` fixos no código, e `CORS(app)` liberado para qualquer origem em rotas que alteram dados.
Impact: O depurador do Werkzeug permite execução de código remoto se exposto, e qualquer site pode chamar as rotas de escrita.
Recommendation: T18 — debug e origens de CORS vindos do ambiente, com default seguro.

### [HIGH] Unauthenticated Write Endpoints (AP-07)
File: app.py:14, app.py:15, app.py:20, app.py:23, app.py:26
Description: Criar/atualizar produto, criar usuário, criar pedido e mudar status de pedido não exigem identidade. `/login` não devolve token nem sessão, então nenhuma rota depende dele.
Impact: Qualquer cliente altera catálogo, preços e status de pedidos.
Recommendation: T08 — guard de escrita por flag para PUT/POST de catálogo e status (POST /usuarios, /login e /pedidos permanecem públicos por serem fluxo de cliente; decisão registrada na Fase 3).

### [HIGH] Business Logic and Data Access Outside a Service Layer (AP-05)
File: app.py:49-55, app.py:66-76, controllers.py:242-250, controllers.py:266-274, models.py:137-146, models.py:256-262
Description: As rotas de admin e o health check abrem conexão e executam SQL direto no handler; o model calcula total do pedido, baixa estoque e aplica as faixas de desconto do relatório; o controller decide status e notificações. Nenhum módulo concentra os três papéis (por isso não é AP-03), mas as camadas estão misturadas.
Impact: A regra de negócio não pode ser testada sem HTTP e banco.
Recommendation: T06 — mover cálculos e decisões para serviços; models só fazem acesso a dados; controllers só traduzem HTTP.

### [HIGH] Shared Global Database Connection (AP-06)
File: database.py:4, database.py:7-10
Description: `db_connection` é global, criada sob demanda com `check_same_thread=False` e compartilhada por todas as requisições.
Impact: Requisições concorrentes compartilham cursor e transação, com risco de commits cruzados e estado corrompido.
Recommendation: T07 — conexão por requisição (`flask.g`) fechada no teardown.

### [MEDIUM] Missing Input Validation (AP-14)
File: app.py:61-62, controllers.py:43-46, controllers.py:87-90, controllers.py:118-121, controllers.py:169-170, controllers.py:239-240, models.py:140-146
Description: `request.get_json()` usado sem checar `None` em `/admin/query`, `/login` e status; `preco`/`estoque` comparados sem checar tipo; `float(preco_min)` sem tratamento; itens do pedido sem checar chaves, tipo ou `quantidade > 0` (quantidade negativa aumenta o estoque).
Impact: Entrada inválida gera 500 em vez de 400, e quantidade negativa corrompe estoque e total.
Recommendation: T17 — validação de tipo, presença e faixa na borda, devolvendo 400.

### [MEDIUM] Generic Error Handling Leaking Internals (AP-09)
File: app.py:77-78, controllers.py:10-12, controllers.py:21-22, controllers.py:60-62, controllers.py:95-96, controllers.py:108-109, controllers.py:125-126, controllers.py:133-134, controllers.py:143-144, controllers.py:164-165, controllers.py:185-186, controllers.py:218-220, controllers.py:226-227, controllers.py:234-235, controllers.py:254-255, controllers.py:261-262, controllers.py:291-292
Description: Cada handler captura `Exception` e devolve `str(e)` ao cliente com 500; não há handler central nem rollback.
Impact: Mensagens internas (SQL, caminhos) vazam e erros de validação viram 500.
Recommendation: T10 — exceções de domínio e error handler central com mensagem genérica para 500.

### [MEDIUM] Duplicated Logic (AP-13)
File: controllers.py:28-50, controllers.py:72-90, models.py:12-21, models.py:31-40, models.py:304-313, models.py:171-201, models.py:203-233
Description: A validação de produto está copiada em criar e atualizar e já diverge (atualizar não valida tamanho do nome nem categoria). A serialização de produto aparece três vezes e a montagem de pedidos com itens duas vezes.
Impact: Correções aplicadas em uma cópia não chegam à outra; já é possível gravar categoria inválida via PUT.
Recommendation: T16 — um validador e um serializador por entidade, reutilizados.

### [MEDIUM] N+1 Queries (AP-08)
File: models.py:139-140, models.py:154-155, models.py:187-193, models.py:219-225
Description: Para cada pedido é feita uma consulta de itens e, para cada item, uma consulta do nome do produto; criar pedido consulta o produto duas vezes por item.
Impact: O número de consultas cresce com pedidos × itens.
Recommendation: T09 — JOIN entre pedidos, itens_pedido e produtos; buscar produtos do pedido em uma consulta `IN`.

### [LOW] Print as Logging and Dead Code (AP-12)
File: app.py:56, app.py:83-86, controllers.py:8, controllers.py:11, controllers.py:57, controllers.py:61, controllers.py:106, controllers.py:161, controllers.py:179, controllers.py:182, controllers.py:208-210, controllers.py:219, controllers.py:248, controllers.py:250, database.py:2, models.py:2
Description: `print` usado como log e como notificação simulada (email, SMS, push); imports `os` e `sqlite3` sem uso; nomes `cursor2`/`cursor3` e `id` sombreando o builtin.
Impact: Logs sem nível nem destino, e ruído na leitura.
Recommendation: T13/T14/T15 — `logging`, remoção de imports mortos e nomes descritivos.

### [LOW] Magic Numbers and Strings (AP-11)
File: controllers.py:52, controllers.py:242, models.py:247-253, models.py:257-262
Description: Categorias válidas, status de pedido e faixas de desconto (10000/0.1, 5000/0.05, 1000/0.02) são literais soltos.
Impact: Mudar uma regra exige caçar literais espalhados.
Recommendation: T12 — constantes nomeadas num módulo de regras.

```
================================
Total: 14 findings
================================
```
