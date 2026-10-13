# Análise manual dos 3 projetos

Revisão feita lendo o código original (antes de qualquer alteração). Linhas conferidas com `grep`/`cat -n`. Os itens seguem o plano em `docs/planos/desafio-4-plano-detalhado.md`; onde a leitura mostrou algo diferente, a correção está marcada com **(corrigido)**.

Mínimo exigido por projeto: ≥ 5 problemas, sendo ≥ 1 CRITICAL ou HIGH, 2 MEDIUM e 2 LOW.

---

## Projeto 1 — `code-smells-project` (Flask + sqlite3, e-commerce)

| Severidade | Problema | Onde | Por que importa |
| --- | --- | --- | --- |
| CRITICAL | SQL injection: consultas montadas por concatenação de strings | `models.py:28`, `47-50`, `109-111`, `140`, `174`, `291-297` | Qualquer valor vindo da requisição (`email`, `senha`, `q`, `categoria`, `nome`) altera a consulta. O login aceita `' OR '1'='1` como senha, por exemplo. |
| CRITICAL | Endpoints de administração sem autenticação: execução de SQL arbitrário e reset do banco | `app.py:47-57` (`/admin/reset-db`), `app.py:59-78` (`/admin/query`) | Qualquer cliente anônimo apaga o banco ou executa qualquer SQL. Combinado com a injeção, a superfície de ataque é total. |
| CRITICAL | `SECRET_KEY` hardcoded, debug ligado em produção | `app.py:7-8`, `app.py:88`, `controllers.py:288-289` | A chave fica no repositório. `/health` devolve a própria chave e `"debug": true` para qualquer um. |
| CRITICAL | Senhas em texto puro, devolvidas nas respostas da API | `database.py:31`, `database.py:76-78` (seed), `models.py:83`, `models.py:99` | Quem lê o banco ou uma resposta de `/usuarios` já tem as senhas. Sem hash, não há como trocar a senha sem vazar o valor antigo. |
| HIGH | Módulo único com dados, regras de negócio e formatação de 4 domínios | `models.py` (314 linhas) | Viola a separação de responsabilidades. Não dá para testar a regra de desconto sem subir o banco. |
| HIGH | Conexão global e mutável, compartilhada entre threads | `database.py:4-10` | `db_connection` é um global criado na primeira chamada e usado por todas as requisições, com `check_same_thread=False`. Concorrência pode corromper transações. |
| MEDIUM | Queries N+1 ao listar pedidos | `models.py:188-192`, `220-224` | Para cada pedido e cada item há uma consulta nova. Com 1000 pedidos, são milhares de viagens ao banco. |
| MEDIUM | Validação de produto duplicada entre criar e atualizar | `controllers.py:28-54` e `controllers.py:72-90` | As mesmas regras estão em dois lugares. Uma correção em um deles deixa o outro errado. |
| LOW | `print` usado como log e como notificação | `controllers.py:8`, `57`, `106`, `161`, `179`, `208-210`, `248-250` | Sem nível, sem destino e sem contexto. Em produção, `ENVIANDO SMS` no stdout não envia nada. |
| LOW | Magic numbers nas faixas de desconto do relatório | `models.py:257-262` | `10000`, `0.1`, `5000`, `0.05` sem nome. Mudar a política exige caçar literais. |

---

## Projeto 2 — `ecommerce-api-legacy` (Express + sqlite3 em memória, LMS com checkout)

| Severidade | Problema | Onde | Por que importa |
| --- | --- | --- | --- |
| CRITICAL | Credenciais de banco e chave do gateway de pagamento de produção hardcoded | `src/utils.js:3-4` (`dbPass`, `paymentGatewayKey`), `src/utils.js:5` (`smtpUser`) | Credenciais reais no código-fonte, versionadas no Git. Qualquer clone tem acesso ao gateway. |
| CRITICAL | Número completo do cartão e chave do gateway escritos no log | `src/AppManager.js:45` | O log guarda PAN (número do cartão). Isso é violação direta de PCI-DSS e vaza o segredo do gateway a quem tiver acesso aos logs. |
| CRITICAL | God class: banco, schema, seed, rotas e regra de pagamento na mesma classe | `src/AppManager.js:4-139` | Não há como testar o checkout sem subir o schema e o servidor. Qualquer mudança na tabela exige mexer no roteamento. |
| HIGH | Hash de senha caseiro e senha padrão `"123456"` quando o campo vem vazio | `src/utils.js:17-23` (`badCrypto`), `src/AppManager.js:68` | `badCrypto` não é um hash: repete base64 e corta em 10 caracteres, então colisões são previsíveis. O fallback para `"123456"` cria contas com senha conhecida. |
| HIGH | Rotas administrativas sem autenticação; excluir usuário deixa matrículas e pagamentos órfãos | `src/AppManager.js:80-129` (relatório financeiro), `src/AppManager.js:131-137` (`DELETE /api/users/:id`) | O relatório financeiro e a exclusão de usuário são públicos. A exclusão não remove `enrollments` nem `payments`, e a própria resposta diz "ficaram sujos no banco". |
| MEDIUM | Callbacks aninhados com N+1 no relatório financeiro | `src/AppManager.js:83-128` | Para cada curso, cada matrícula e cada pagamento há uma consulta. A contagem de pendentes é controlada à mão, o que é frágil para qualquer mudança. |
| MEDIUM | Erros de banco ignorados nos callbacks | `src/AppManager.js:92`, `104`, `106`, `133` | O `err` é recebido e não verificado. Falha de leitura vira relatório parcial ou matrícula "Unknown" sem aviso. |
| MEDIUM | Estado global mutável (`globalCache`, `totalRevenue`) | `src/utils.js:9-10`, `src/utils.js:12-15` | `logAndCache` escreve em um objeto de módulo compartilhado. O `totalRevenue` é importado mas nunca é usado, então parece dado e não é. |
| LOW | Nomes de variáveis ilegíveis | `src/AppManager.js:29-33` (`u`, `e`, `p`, `cid`, `cc`) | Com `cc` e `p` no mesmo bloco, ninguém lê rápido que um é o cartão e outro a senha. |
| LOW | Magic strings de status e regra do cartão ("começa com 4") | `src/AppManager.js:46` (`"4"`, `"PAID"`, `"DENIED"`) | A regra de aprovação é um `startsWith` com literal. Status como string solta permitem erro de digitação sem aviso. |

**Observação extra (não entra na contagem):** o checkout cria o usuário em `src/AppManager.js:66-72` **antes** de validar o pagamento (linha 46-48). Um pagamento recusado deixa a conta criada.

---

## Projeto 3 — `task-manager-api` (Flask + SQLAlchemy, já com camadas)

| Severidade | Problema | Onde | Por que importa |
| --- | --- | --- | --- |
| CRITICAL | Senha com hash MD5, sem salt | `models/user.py:29`, `models/user.py:32` | MD5 é rápido demais e sem salt, então tabelas pré-calculadas quebram a maioria das senhas em segundos. |
| CRITICAL | `to_dict` do usuário devolve o hash da senha | `models/user.py:21` | `GET /users`, `GET /users/<id>` e `POST /login` expõem o campo `password` com o hash. Combinado com o MD5, é o vazamento completo. |
| CRITICAL | `SECRET_KEY` e credenciais de SMTP hardcoded | `app.py:13`, `services/notification_service.py:7-10` | Chave de sessão e senha do e-mail (`senha123`) no código. |
| HIGH | Regra de negócio dentro das rotas, sem camada de controller | `routes/task_routes.py:12-63` (cálculo de atraso e enriquecimento), `routes/report_routes.py:13-101` (relatório inteiro) | Cada handler faz validação, consulta, cálculo e formatação. Testar o relatório exige subir o Flask. |
| HIGH | Login devolve um token falso, sem autenticação real | `routes/user_routes.py:210` (`'fake-jwt-token-' + str(user.id)`) | O token é previsível (basta o id) e nenhuma rota o verifica. Quem sabe um id tem "sessão". |
| MEDIUM | Queries N+1 ao montar tarefas, usuários e relatórios | `routes/task_routes.py:42`, `51`; `routes/report_routes.py:55-59`, `163`; `routes/user_routes.py:22` (`len(u.tasks)`) | Consulta por tarefa para o usuário e a categoria; consulta por usuário para as tarefas dele; `len(u.tasks)` carrega a relação inteira só para contar. |
| MEDIUM | `except:` genérico engolindo erros | `routes/task_routes.py:62`, `137`, `204`, `236`; `routes/user_routes.py:130`, `149`; `routes/report_routes.py:186`, `207`, `221`; `utils/helpers.py:46`, `49`, `88` | Erro de banco vira "Erro interno" sem log. Em `parse_date`, qualquer exceção vira `None`. |
| MEDIUM | APIs deprecated: `datetime.utcnow()` e `Query.get()` | `models/task.py:15-16`, `models/task.py:52`, `models/user.py:14`, `models/category.py:11`, `services/notification_service.py:35`, `utils/helpers.py:38`; `Query.get` em 16 pontos: `routes/task_routes.py:42`, `51`, `67`, `117`, `122`, `158`, `188`, `195`, `227`; `routes/user_routes.py:29`, `94`, `136`, `155`; `routes/report_routes.py:105`, `192`, `213` | `utcnow` está deprecated desde o Python 3.12 e devolve datetime naive. `Query.get` está deprecated no SQLAlchemy 2.0 em favor de `session.get`. O `seed.py` também dispara o warning. |
| LOW | Imports não usados | `app.py:7` (`os, sys, json, datetime`), `routes/task_routes.py:7` (`json, os, sys, time`), `utils/helpers.py:3-6`, `models/task.py:3` (`json`) | Ruído, e `datetime` importado em `app.py` sugere que o módulo tem lógica de data que não existe. |
| LOW | `print` como log e condicionais redundantes | `routes/task_routes.py:149`, `219`, `234`; `models/task.py:50-60` (`is_overdue` com quatro `if` aninhados) | Mesmo problema do projeto 1. `is_overdue` pode virar uma expressão de uma linha. |

**Problemas extras encontrados na releitura (não entram na contagem mínima):**

- **MEDIUM — lógica de "atrasada" duplicada em 6 lugares:** `routes/task_routes.py:30-37`, `71-80`, `282-287`; `routes/user_routes.py:171-180`; `routes/report_routes.py:34-37`, `132-135`. (Corrige o plano, que dizia 5.)
- **MEDIUM — PUT de categoria sem validar o corpo:** `routes/report_routes.py:196-197` faz `'name' in data` com `data = None` quando o body não é JSON, o que gera 500.
