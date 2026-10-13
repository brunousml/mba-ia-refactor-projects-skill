# Análise manual dos 3 projetos

Revisão feita sobre o código original, antes de qualquer alteração. As linhas foram conferidas com `cat -n` e `grep`, e a análise passou por uma revisão independente, feita por subagentes, no checkpoint 1. A coluna **AP** aponta o anti-pattern correspondente no catálogo da skill (`.claude/skills/refactor-arch/references/anti-patterns-catalog.md`). Ela é a base para conferir se a Fase 2 encontra os mesmos problemas.

Mínimo exigido por projeto: ≥ 5 problemas, sendo ≥ 1 CRITICAL ou HIGH, 2 MEDIUM e 2 LOW.

---

## Projeto 1 — `code-smells-project` (Flask + sqlite3, e-commerce)

| Severidade | AP | Problema | Onde | Por que importa |
| --- | --- | --- | --- | --- |
| CRITICAL | AP-02 | SQL injection: consultas montadas por concatenação com valores vindos do JSON ou da query string | `models.py:47-50`, `57-61`, `109-111`, `126-129`, `140`, `148-151`, `157-166`, `291-297` | `nome`, `descricao`, `categoria`, `email`, `senha`, `q`, `produto_id` e `quantidade` chegam crus à consulta. No login, a senha `' OR '1'='1` autentica como o primeiro usuário (o admin do seed). As concatenações com `id` vindo do caminho (`models.py:28`, `174`) não são exploráveis, porque o conversor `<int:>` da rota garante um inteiro. |
| CRITICAL | AP-07 | Endpoints de administração sem autenticação: execução de SQL arbitrário e reset do banco | `app.py:47-57` (`/admin/reset-db`), `app.py:59-78` (`/admin/query`) | Qualquer cliente anônimo apaga o banco ou executa qualquer SQL. |
| CRITICAL | AP-01 | `SECRET_KEY` hardcoded e exposta pelo health check | `app.py:7`, `controllers.py:288-289` | A chave está no repositório, e `/health` a devolve a qualquer um junto com `"debug": true`. |
| CRITICAL | AP-04 | Senhas em texto puro, gravadas e devolvidas pela API | `database.py:31`, `database.py:76-78` (seed), `models.py:126-129` (gravação), `models.py:83`, `99` (resposta) | Quem lê o banco ou chama `GET /usuarios` obtém senhas reutilizáveis na hora, sem quebrar hash nenhum. |
| HIGH | AP-15 | Debug ligado no código | `app.py:8`, `app.py:88` | O modo debug do servidor de desenvolvimento expõe o depurador interativo, que permite execução remota de código. |
| HIGH | AP-05 | Módulo único com acesso a dados, regra de negócio e formatação de 4 domínios | `models.py` (314 linhas) | Viola a separação de responsabilidades: a regra de desconto só é testável subindo o banco. É HIGH, e não CRITICAL, porque o módulo não registra rotas (falha o item (c) do AP-03). |
| HIGH | AP-06 | Conexão global e mutável, compartilhada entre threads | `database.py:4-10` | Todas as requisições usam a mesma conexão (`check_same_thread=False`). Se `criar_pedido` falha no meio, os INSERTs pendentes ficam na conexão, e o próximo `commit()` de outra requisição grava um pedido parcial. |
| MEDIUM | AP-08 | Queries N+1 ao listar pedidos | `models.py:188-192`, `220-224` | Uma consulta por pedido e outra por item. Com 1000 pedidos, são milhares de viagens ao banco. |
| MEDIUM | AP-13 | Validação de produto duplicada entre criar e atualizar, e as cópias já divergem | `controllers.py:28-54` e `controllers.py:72-90` | A atualização não valida o tamanho do nome (`47-50`) nem a categoria (`52-54`): `controllers.py:85` aceita qualquer valor. É exatamente o risco da duplicação. |
| MEDIUM | AP-14 | Quantidade do pedido sem validação | `models.py:144`, `146`, `164` | Uma quantidade negativa passa no teste de estoque, gera total negativo e **aumenta** o estoque. |
| MEDIUM | AP-09 | Mensagem interna da exceção devolvida ao cliente | `controllers.py:12`, `22`, `62` e demais `except Exception as e` | O `str(e)` revela erros do SQL e facilita explorar a injeção. Também não existe handler central. |
| LOW | AP-12 | `print` usado como log e como notificação | `controllers.py:8`, `57`, `106`, `161`, `179`, `208-210`, `248-250` | Sem nível, destino ou contexto. `ENVIANDO SMS` no stdout não envia nada. |
| LOW | AP-11 | Magic numbers nas faixas de desconto do relatório | `models.py:257-262` | `10000`, `0.1`, `5000`, `0.05`, `1000` e `0.02` sem nome. Mudar a política exige caçar literais. |

---

## Projeto 2 — `ecommerce-api-legacy` (Express + sqlite3 em memória, LMS com checkout)

| Severidade | AP | Problema | Onde | Por que importa |
| --- | --- | --- | --- | --- |
| CRITICAL | AP-01 | Credenciais de banco e chave de produção do gateway de pagamento hardcoded | `src/utils.js:2-4` (`dbUser`, `dbPass`, `paymentGatewayKey`) | Credenciais reais no código-fonte e versionadas. Qualquer clone tem acesso ao gateway. |
| CRITICAL | AP-04 | Número completo do cartão e chave do gateway escritos no log | `src/AppManager.js:45` | O log guarda o número do cartão (PAN), em violação direta do PCI-DSS, e vaza o segredo do gateway. |
| CRITICAL | AP-04 | Hash de senha caseiro | `src/utils.js:17-23` (`badCrypto`) | Não é hash: repete um prefixo base64 e corta em 10 caracteres. Senhas com o mesmo começo colidem, e o valor é reversível na prática. |
| CRITICAL | AP-03 | God class: banco, schema, seed, rotas e regra de pagamento na mesma classe | `src/AppManager.js:4-139` | Não dá para testar o checkout sem subir schema e servidor. Mudar uma tabela exige mexer no roteamento. |
| CRITICAL | AP-07 | Rotas de administração e de exclusão públicas | `src/AppManager.js:80-129` (relatório financeiro), `src/AppManager.js:131-137` (`DELETE /api/users/:id`) | Qualquer um apaga usuários e lê nomes de alunos e valores pagos. A exclusão deixa matrículas e pagamentos órfãos, e a própria resposta admite isso. |
| HIGH | AP-06 | Estado global mutável | `src/utils.js:9-10`, `src/utils.js:12-15` | `logAndCache` escreve num objeto de módulo compartilhado. `totalRevenue` é exportado e importado, mas nunca usado: parece dado e não é. |
| HIGH | AP-15 | Senha padrão `"123456"` quando o campo vem vazio | `src/AppManager.js:68` | Contas criadas no checkout sem senha ficam com uma senha conhecida por todos. |
| MEDIUM | AP-08 | Callbacks aninhados com N+1 no relatório financeiro | `src/AppManager.js:83-128` | Uma consulta por curso, por matrícula e por pagamento. O contador de pendentes é mantido à mão, o que é frágil. |
| MEDIUM | AP-09 | Erros de banco ignorados nos callbacks | `src/AppManager.js:57`, `92`, `104`, `106`, `133` | Na linha 92, se a consulta falhar, `enrollments` fica `undefined` e `enrollments.length` (linha 93) lança `TypeError` dentro do callback. O Express não captura o erro e o processo Node cai. Na linha 57, a falha do audit log é ignorada e a resposta sai 200. |
| LOW | AP-12 | Nomes de variáveis ilegíveis | `src/AppManager.js:29-33` (`u`, `e`, `p`, `cid`, `cc`) | Com `cc` e `p` no mesmo bloco, quem lê não percebe rápido que um é o cartão e o outro a senha. |
| LOW | AP-11 | Magic strings de status e regra do cartão ("começa com 4") | `src/AppManager.js:46` (`"4"`, `"PAID"`, `"DENIED"`) | A regra de aprovação é um `startsWith` com literal, e status em string solta deixam passar erro de digitação. |

**Observações extras (não entram na contagem):**
- O checkout cria o usuário (`src/AppManager.js:66-72`) **antes** de validar o pagamento (linhas 46-48). Um pagamento recusado deixa a conta criada.
- Checkout com e-mail já existente não confere a senha (`src/AppManager.js:73-74`). Basta saber o e-mail de alguém para matricular ou cobrar na conta dessa pessoa.

---

## Projeto 3 — `task-manager-api` (Flask + SQLAlchemy, já com camadas)

| Severidade | AP | Problema | Onde | Por que importa |
| --- | --- | --- | --- | --- |
| CRITICAL | AP-04 | Senha com hash MD5, sem salt | `models/user.py:29`, `models/user.py:32` | MD5 é rápido demais e sem salt. Tabelas pré-calculadas quebram a maioria das senhas em segundos. |
| CRITICAL | AP-04 | `to_dict` do usuário devolve o hash da senha | `models/user.py:21`, usado em `routes/user_routes.py:33`, `85`, `129`, `209` | `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login` expõem o hash. `GET /users` monta um dicionário próprio sem o campo (`user_routes.py:15-23`). Junto com o MD5, o vazamento é completo. |
| CRITICAL | AP-15 | Qualquer anônimo cria ou promove um usuário a `admin` | `routes/user_routes.py:52`, `71-72` (criação), `119-122` (atualização) | O papel vem do corpo da requisição, sem nenhuma autenticação. É mais grave que o token falso, porque dá privilégio total a quem pedir. |
| CRITICAL | AP-01 | `SECRET_KEY` e credenciais de SMTP hardcoded | `app.py:13`, `services/notification_service.py:7-10` | A chave de sessão e a senha do e-mail (`senha123`) estão no código. |
| HIGH | AP-05 | Regra de negócio dentro das rotas, sem camada de controller | `routes/task_routes.py:12-63` (atraso e enriquecimento), `routes/report_routes.py:13-101` (relatório inteiro) | Cada handler valida, consulta, calcula e formata. Para testar o relatório é preciso subir o Flask. |
| HIGH | AP-07 | Login devolve um token falso, e nenhuma rota exige autenticação | `routes/user_routes.py:210` (`'fake-jwt-token-' + str(user.id)`) | O token é previsível (basta o id) e ninguém o verifica. |
| MEDIUM | AP-08 | Queries N+1 ao montar tarefas, usuários e relatórios | `routes/task_routes.py:42`, `51`; `routes/report_routes.py:55-59`, `163`; `routes/user_routes.py:22` (`len(u.tasks)`) | Uma consulta por tarefa para o usuário e a categoria, e outra por usuário para as tarefas. `len(u.tasks)` carrega a relação inteira só para contar. |
| MEDIUM | AP-09 | `except:` genérico engolindo erros | `routes/task_routes.py:62`, `137`, `204`, `236`; `routes/user_routes.py:130`, `149`; `routes/report_routes.py:186`, `207`, `221`; `utils/helpers.py:46`, `49`, `88` | Erro de banco vira "Erro interno" sem log. Em `parse_date`, qualquer exceção vira `None`. |
| MEDIUM | AP-10 | APIs deprecated: `datetime.utcnow` e `Query.get()` | `utcnow`: `models/task.py:15-16`, `52`; `models/user.py:14`; `models/category.py:11`; `services/notification_service.py:35`; `utils/helpers.py:38`. `Query.get` em 16 pontos: `routes/task_routes.py:42`, `51`, `67`, `117`, `122`, `158`, `188`, `195`, `227`; `routes/user_routes.py:29`, `94`, `136`, `155`; `routes/report_routes.py:105`, `192`, `213` | `utcnow` está deprecated desde o Python 3.12 (o `seed.py` já dispara o warning). `Query.get` é API legada no SQLAlchemy 2.0, substituída por `session.get`. Nos models, `utcnow` aparece como referência (`default=datetime.utcnow`), não como chamada. |
| MEDIUM | AP-13 | Regra de "atrasada" duplicada em 6 lugares, e o método do model que a implementa é código morto | `routes/task_routes.py:30-37`, `71-80`, `282-287`; `routes/user_routes.py:171-180`; `routes/report_routes.py:34-37`, `132-135`; `models/task.py:50-60` (`is_overdue`, nunca chamado) | Seis cópias da mesma regra: qualquer ajuste precisa ser feito em todas. |
| MEDIUM | AP-14 | Tipo de entrada não validado | `routes/task_routes.py:113`, `182` (`priority` comparado com int), `261` (`int(priority)` sem tratamento); `routes/report_routes.py:196-197` | `priority` vindo como string lança `TypeError` e devolve 500. No PUT de categoria, corpo JSON `null` faz `'name' in data` falhar (500). Sem JSON, o Flask devolve 415. |
| LOW | AP-12 | Imports não usados | `app.py:7` (`os, sys, json`), `routes/task_routes.py:7` (`json, os, sys, time`), `routes/user_routes.py:6` (`hashlib, json`), `routes/report_routes.py:7-8` (`format_date`, `calculate_percentage`, `json`), `utils/helpers.py:3-7`, `models/task.py:3` (`json`) | Ruído que esconde as dependências reais de cada módulo. |
| LOW | AP-12 | `print` como log e condicionais redundantes | `routes/task_routes.py:149`, `219`, `234`; `models/task.py:50-60` (três `if` aninhados) | O mesmo problema do projeto 1. `is_overdue` caberia numa expressão de uma linha. |

**Observação extra:** `debug=True` em `app.py:34` (AP-15) aparece só quando o servidor sobe com `python app.py`.

---

## Resumo por projeto

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
| --- | --- | --- | --- | --- | --- |
| 1 — code-smells-project | 4 | 3 | 4 | 2 | 13 |
| 2 — ecommerce-api-legacy | 5 | 2 | 2 | 2 | 11 |
| 3 — task-manager-api | 4 | 2 | 5 | 2 | 13 |
