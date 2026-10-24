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
CRITICAL: 5 | HIGH: 4 | MEDIUM: 4 | LOW: 2

## Findings

### [CRITICAL] Hardcoded Credentials (AP-01)
File: app.py:7, database.py:76-78, controllers.py:289
Description: A `SECRET_KEY` do Flask é um literal no código, e o mesmo valor volta no corpo do `/health` (controllers.py:289). O seed grava senhas de exemplo (`admin123`, `123456`, `senha123`) direto no código (database.py:76-78).
Impact: Quem lê o repositório ou chama `/health` obtém a chave da aplicação.
Recommendation: T01 — ler `SECRET_KEY` de variável de ambiente num módulo de config e tirar o valor do health check.

### [CRITICAL] Unauthenticated Destructive and Sensitive Reads (AP-07)
File: app.py:18-19, app.py:24-25, app.py:28, app.py:30, app.py:47-57, app.py:59-78
Description: Nenhuma dessas rotas verifica identidade. `POST /admin/reset-db` apaga as quatro tabelas; `POST /admin/query` executa o SQL recebido no corpo (app.py:69); `GET /usuarios` e `GET /usuarios/<id>` devolvem dados pessoais e senha; `GET /pedidos` e `GET /pedidos/usuario/<id>` devolvem pedidos de qualquer cliente; `GET /relatorios/vendas` devolve dados financeiros; `GET /health` devolve a chave secreta.
Impact: Qualquer cliente anônimo apaga o banco, executa SQL arbitrário ou lê dados pessoais e financeiros.
Recommendation: T08 — guard de administração (reset, query), de leitura sensível (usuários, pedidos, relatório) e remoção da chave do health, controlados por flag e `X-Admin-Token`.
Nota da Fase 3: `GET /relatorios/vendas` ficou no guard de administração, e não no de leitura sensível. A regra do T08 manda relatório e exportação para administração, mesmo com valores financeiros.

### [CRITICAL] SQL Injection (AP-02)
File: app.py:69, models.py:48-49, models.py:58-60, models.py:110, models.py:127-128, models.py:140, models.py:149-150, models.py:155, models.py:158-160, models.py:164-165, models.py:291, models.py:293
Description: Estas consultas recebem texto do cliente por concatenação: `nome`, `descricao` e `categoria` (criar e atualizar produto), `email` e `senha` (login e cadastro), `produto_id` e `usuario_id` (pedido), `q` e `categoria` (busca). O `categoria` do PUT não passa por lista válida (controllers.py:81-85). `/admin/query` executa o SQL do corpo. As concatenações com `id` vindo de `<int:...>` (models.py:28, 68, 92, 174), com valores do próprio banco (models.py:188, 192, 220, 224), com `status` validado por lista (models.py:280) e com `preco_min`/`preco_max` convertidos por `float` (models.py:295, 297) são má prática, mas não são exploráveis.
Impact: Bypass de login (`' OR '1'='1`), leitura e alteração arbitrária do banco.
Recommendation: T02 — consultas parametrizadas (`?`) em todo o models.py, e remoção ou guard do executor de SQL (`/admin/query`).

### [CRITICAL] God Module (AP-03)
File: controllers.py:3, controllers.py:242-250, controllers.py:264-274, controllers.py:52-54
Description: `controllers.py` importa a camada de dados (`models`, `get_db`) e o transporte (Flask). Executa SQL direto no health check (264-274), decide o efeito de cada status de pedido e imprime notificações conforme o status (242-250), e mantém a lista de categorias válidas como regra de negócio (52-54). Os três papéis estão no mesmo módulo.
Impact: Qualquer mudança de regra ou de consulta mexe no arquivo das rotas, e testar a regra exige HTTP e banco.
Recommendation: T03 (separar camadas) e T06 (tirar decisão e regra do controller).

### [CRITICAL] Sensitive Data Exposure and Plaintext Passwords (AP-04)
File: models.py:83, models.py:99, models.py:110, models.py:127-128, database.py:76-78, controllers.py:289
Description: Senhas são gravadas e comparadas em texto puro (models.py:127-128 e 110). `get_todos_usuarios` (models.py:83) e `get_usuario_por_id` (models.py:99) incluem `senha`, que sai em `GET /usuarios` e `GET /usuarios/<id>`. `/health` devolve `secret_key` (controllers.py:289).
Impact: Quem chama a API ou lê o banco obtém todas as senhas.
Recommendation: T04 (hash com salt, refazendo o seed com as mesmas senhas de exemplo) e T05 (serialização sem `senha` e sem chave).

### [HIGH] Insecure Configuration (AP-15)
File: app.py:8, app.py:9, app.py:88
Description: `DEBUG = True` (app.py:8) e `app.run(debug=True)` (app.py:88) estão fixos no código, e `host="0.0.0.0"` no mesmo `run` (app.py:88) expõe a aplicação na rede. `CORS(app)` (app.py:9) libera qualquer origem para todas as rotas, inclusive as de escrita.
Impact: Com o host em `0.0.0.0`, o depurador do Werkzeug fica acessível pela rede (protegido só por PIN), e qualquer site pode chamar as rotas de escrita.
Recommendation: T18 — debug, host e origens de CORS vindos do ambiente, com default seguro.

### [HIGH] Unauthenticated Write Endpoints (AP-07)
File: app.py:14-16, app.py:23, app.py:26, controllers.py:195-203, controllers.py:167-186
Description: Criar, alterar e apagar produto (app.py:14-16), criar pedido (app.py:23) e mudar status de pedido (app.py:26) não exigem identidade. Em `POST /pedidos`, o `usuario_id` vem do corpo e o pedido é criado para qualquer conta existente, sem conferir senha (controllers.py:195-203). O `/login` (controllers.py:167-186) não devolve token nem sessão, então nenhuma rota depende dele.
Impact: Qualquer cliente altera catálogo, preços e estoque, muda o status de pedidos e cria pedidos em nome de outros usuários.
Recommendation: T08 — guard de escrita por flag para PUT/DELETE/POST de catálogo e status. `POST /pedidos` deve obter o usuário da credencial do dono, não do corpo. Decisão a registrar na Fase 3: `POST /usuarios` e `/login` seguem públicos por serem fluxo de cliente.
Nota da Fase 3: o contrato original de `POST /pedidos` não envia credencial do dono, então a proteção é o guard de escrita (regra da conta existente no T08). `POST /usuarios` também ficou atrás do guard de escrita, por decisão do usuário. `/login` segue público.

### [HIGH] Business Logic and Data Access Outside the Route and Data Layers (AP-05)
File: app.py:49-55, app.py:66-76, models.py:137-169, models.py:256-262
Description: As rotas de admin abrem conexão e executam SQL no próprio handler (app.py:49-55, 66-76). O model calcula o total do pedido, valida e baixa o estoque (models.py:137-169) e aplica as faixas de desconto do relatório (models.py:256-262).
Impact: A regra de negócio não pode ser testada sem banco, e mudar uma regra exige mexer na camada de dados.
Recommendation: T06 — mover cálculo, estoque e desconto para um serviço; models só acessam dados; rotas de admin passam pelo model.

### [HIGH] Shared Global Database Connection (AP-06)
File: database.py:4, database.py:7-10
Description: `db_connection` é global, criada sob demanda (database.py:7-10) com `check_same_thread=False`, e compartilhada por todas as requisições.
Impact: Requisições concorrentes compartilham cursor e transação, com risco de commits cruzados e estado corrompido.
Recommendation: T07 — conexão por requisição (`flask.g`), fechada no teardown.

### [MEDIUM] Missing Input Validation (AP-14)
File: app.py:61-62, controllers.py:43-46, controllers.py:87-90, controllers.py:118-121, controllers.py:169-170, controllers.py:239-240, models.py:144-146
Description: `request.get_json()` é usado sem checar `None` em `/admin/query` (app.py:61-62), `/login` (controllers.py:169-170) e status (controllers.py:239-240). `preco` e `estoque` são comparados sem checar tipo (controllers.py:43-46, 87-90). `float(preco_min)` e `float(preco_max)` não têm tratamento (controllers.py:118-121). Itens do pedido não têm faixa de `quantidade` (models.py:144-146): quantidade negativa passa na checagem de estoque, aumenta o estoque e gera total negativo.
Impact: Entrada inválida gera 500 em vez de 400, e quantidade negativa corrompe estoque e total.
Recommendation: T17 — validação de tipo, presença e faixa na borda, devolvendo 400.

### [MEDIUM] Generic Error Handling Leaking Internals (AP-09)
File: app.py:77-78, controllers.py:10-12, controllers.py:21-22, controllers.py:60-62, controllers.py:95-96, controllers.py:108-109, controllers.py:125-126, controllers.py:133-134, controllers.py:143-144, controllers.py:164-165, controllers.py:185-186, controllers.py:218-220, controllers.py:226-227, controllers.py:234-235, controllers.py:254-255, controllers.py:261-262, controllers.py:291-292
Description: Cada handler captura `Exception` e devolve `str(e)` ao cliente com 500. Não há handler central. `criar_pedido` (models.py:133-169) não faz rollback se uma etapa falhar após os primeiros INSERTs.
Impact: Mensagens internas (SQL, caminhos) vazam, e erros de validação viram 500.
Recommendation: T10 — exceções de domínio e error handler central, com mensagem genérica para 500.

### [MEDIUM] Duplicated Logic (AP-13)
File: controllers.py:28-50, controllers.py:72-90, models.py:12-21, models.py:31-40, models.py:304-313, models.py:171-201, models.py:203-233
Description: A validação de produto está copiada em `criar_produto` e `atualizar_produto` e já diverge: a atualização não confere o tamanho do nome (controllers.py:47-50) nem a categoria (controllers.py:52-54). O mesmo mapeamento de produto aparece três vezes (models.py:12-21, 31-40, 304-313), e a montagem de pedido com itens aparece duas vezes (models.py:171-201, 203-233).
Impact: Correções aplicadas em uma cópia não chegam à outra. Hoje já é possível gravar categoria inválida via PUT.
Recommendation: T16 — um validador e um serializador por entidade, reutilizados.

### [MEDIUM] N+1 Queries (AP-08)
File: models.py:139-140, models.py:154-155, models.py:187-193, models.py:219-225
Description: Em `get_pedidos_usuario` e `get_todos_pedidos`, para cada pedido há uma consulta de itens e, para cada item, uma consulta do nome do produto (models.py:187-193, 219-225). `criar_pedido` consulta o mesmo produto duas vezes por item (models.py:139-140, 154-155).
Impact: O número de consultas cresce com pedidos × itens.
Recommendation: T09 — JOIN entre pedidos, itens_pedido e produtos, ou consulta única com `IN`.

### [LOW] Print as Logging and Dead Code (AP-12)
File: app.py:56, app.py:83-86, controllers.py:8, controllers.py:11, controllers.py:57, controllers.py:61, controllers.py:106, controllers.py:161, controllers.py:179, controllers.py:182, controllers.py:208-210, controllers.py:219, controllers.py:248, controllers.py:250, database.py:2, models.py:2
Description: `print` serve de log (controllers.py:8, 11, 57 e outros) e de notificação simulada (controllers.py:208-210). `import os` (database.py:2) e `import sqlite3` (models.py:2) não são usados. O nome `id` (models.py:24, 54, 65, 89; controllers.py:14, 64) sombreia o builtin.
Impact: Logs sem nível nem destino, e ruído na leitura.
Recommendation: T13, T14 e T15 — `logging`, remoção dos imports mortos e nomes descritivos.

### [LOW] Magic Numbers and Strings (AP-11)
File: controllers.py:47-50, controllers.py:52, controllers.py:242, models.py:247-253, models.py:257-262
Description: Limites de tamanho do nome (2 e 200), categorias válidas, status de pedido e faixas de desconto (10000/0.1, 5000/0.05, 1000/0.02) são literais soltos.
Impact: Mudar uma regra exige caçar literais espalhados pelo código.
Recommendation: T12 — constantes nomeadas num módulo de regras.

```
================================
Total: 15 findings
================================
```
