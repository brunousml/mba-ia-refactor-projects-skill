# Desafio: skill `refactor-arch`

Uma skill do Claude Code que audita um projeto de backend e o refatora para MVC, em três fases:

1. **Análise:** detecta a stack e mapeia a arquitetura.
2. **Auditoria:** cruza o código com um catálogo de anti-patterns e gera um relatório. Depois **pausa** e pede confirmação.
3. **Refatoração:** reestrutura o projeto e valida que a aplicação sobe e responde como antes.

A mesma skill, byte a byte, foi executada nos 3 projetos: dois em Python/Flask e um em Node.js/Express.

| O que | Onde |
| --- | --- |
| Skill (cópias idênticas, `diff -r` vazio) | [`code-smells-project/.claude/skills/refactor-arch/`](code-smells-project/.claude/skills/refactor-arch/), [`ecommerce-api-legacy/…`](ecommerce-api-legacy/.claude/skills/refactor-arch/), [`task-manager-api/…`](task-manager-api/.claude/skills/refactor-arch/) |
| Relatórios da Fase 2 | [`reports/audit-project-1.md`](reports/audit-project-1.md), [`-2.md`](reports/audit-project-2.md), [`-3.md`](reports/audit-project-3.md) |
| Logs das execuções, linha de base e comparações | [`docs/runs/`](docs/runs/), [`docs/baseline/`](docs/baseline/) |
| Diário de execução (decisões, desvios, evidências) | [`docs/HANDOFF.md`](docs/HANDOFF.md) |
| Enunciado original | [`docs/ENUNCIADO.md`](docs/ENUNCIADO.md) |

---

## A) Análise Manual

Feita sobre o código original, antes de escrever a skill. As linhas foram conferidas com `cat -n` e `grep`. A análise passou por uma revisão independente, feita por subagentes, e foi corrigida a partir dela. A coluna **AP** liga cada problema ao anti-pattern correspondente do [catálogo da skill](code-smells-project/.claude/skills/refactor-arch/references/anti-patterns-catalog.md). Essa ligação permitiu conferir, depois, se a Fase 2 encontrava os mesmos problemas.

### Projeto 1 — `code-smells-project` (Flask + sqlite3, e-commerce)

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


### Projeto 2 — `ecommerce-api-legacy` (Express + sqlite3 em memória, LMS com checkout)

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


### Projeto 3 — `task-manager-api` (Flask + SQLAlchemy, já com camadas)

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


### Resumo por projeto

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
| --- | --- | --- | --- | --- | --- |
| 1 — code-smells-project | 4 | 3 | 4 | 2 | 13 |
| 2 — ecommerce-api-legacy | 5 | 2 | 2 | 2 | 11 |
| 3 — task-manager-api | 4 | 2 | 5 | 2 | 13 |

---

## B) Construção da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                          orquestração das 3 fases e regras duras (127 linhas)
└── references/
    ├── project-analysis.md           Fase 1: manifestos, imports, banco, rotas, arquitetura, boot/porta/seed
    ├── anti-patterns-catalog.md      Fase 2: 15 anti-patterns com sinais de detecção e severidade
    ├── audit-report-template.md      Fase 2: formato exato do relatório
    ├── mvc-guidelines.md             Fase 3: camadas, responsabilidades, ordem de aplicação, checklist
    └── refactoring-playbook.md       Fase 3: 18 transformações com antes/depois em Python e JavaScript
```

Cada uma das 5 áreas de conhecimento obrigatórias tem o seu arquivo.

### Decisões de design

- **`SKILL.md` curto e imperativo.** Ele diz *o que* fazer em cada fase e *qual* referência carregar. O conhecimento fica nas references, que são lidas só na fase que precisa delas. Assim o contexto da Fase 1 não carrega o playbook inteiro.
- **Regras duras no topo do `SKILL.md`:**
  - as Fases 1 e 2 são só leitura (nada de instalar nem executar);
  - toda linha citada é conferida com leitura do arquivo;
  - a Fase 2 termina em `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e encerra o turno;
  - a Fase 3 preserva o contrato: caminhos, métodos, formato das respostas e porta.
- **A validação da Fase 3 é feita contra o próprio código original.** Antes de mexer em qualquer arquivo, a skill:
  1. sobe o projeto original;
  2. confirma com `lsof` que a porta é da aplicação, e não de outro serviço;
  3. roda o seed, ou faz backup do banco;
  4. grava um snapshot de todas as rotas do inventário (as destrutivas por último) num diretório temporário **fora** do projeto.

  Depois de cada grupo de transformações, ela sobe de novo e compara status e estrutura do corpo. As diferenças precisam ser intencionais e listadas.
- **Uma ordem única de aplicação**, para que o projeto continue subindo a cada passo:
  1. mover para camadas, sem mudar lógica;
  2. segurança: T01, T02, T04, T05, T08, T18;
  3. estrutura: T06, T07, T10, T16, T17;
  4. limpeza: T09, T11–T15.
- **Mudanças de segurança que alteram o contrato são intencionais e documentadas.** Exemplos: rotas de administração continuam registradas, mas respondem 403 por padrão; com `ENABLE_ADMIN_ROUTES=true`, exigem `X-Admin-Token`. Hash de senha deixa de ser devolvido. Senhas passam a ter hash forte, com o seed recriado com as mesmas senhas de exemplo. Isso permite validar duas vezes: com a flag desligada, só as mudanças intencionais divergem; com a flag ligada e o token, o comportamento original volta.
- **Relatório no formato do enunciado:**
  - box `ARCHITECTURE AUDIT REPORT`;
  - `Summary` por severidade;
  - `### [SEV] Title (AP-XX)` com `File:`, `Description:`, `Impact:`, `Recommendation:` (que aponta a transformação do playbook);
  - fechamento `Total: N findings`.

  Há um finding por anti-pattern, com todos os `arquivo:linha` do problema.

### Catálogo de anti-patterns (15)

| Severidade | Anti-patterns | Por que estão aqui |
| --- | --- | --- |
| CRITICAL | AP-01 credenciais hardcoded · AP-02 SQL injection · AP-03 god class/module · AP-04 dados sensíveis expostos e hash fraco | São os exemplos de CRITICAL do enunciado e aparecem nos 3 projetos. O AP-02 só conta valor controlado pelo cliente (um `<int:id>` concatenado não é explorável). O AP-03 exige os três itens: dados, regra e roteamento; com menos que isso, o problema é AP-05. |
| HIGH | AP-05 regra de negócio na rota · AP-06 estado global mutável · AP-07 endpoint sem autenticação · AP-15 configuração insegura | Violações de MVC e SOLID citadas no enunciado. AP-07 e AP-15 sobem para CRITICAL só por critério objetivo: operação destrutiva, dado sensível ou concessão de privilégio. Não há promoção genérica de severidade. |
| MEDIUM | AP-08 N+1 · AP-09 erro genérico/engolido · AP-10 **API deprecated** · AP-13 lógica duplicada · AP-14 validação ausente | Performance, padronização e duplicação. O AP-10 traz uma tabela por ecossistema (Python, SQLAlchemy, Node/Express) com o equivalente moderno. Também detecta referências sem chamada (`default=datetime.utcnow`). |
| LOW | AP-11 magic numbers/strings · AP-12 nomes ruins, código morto, `print` como log | Legibilidade. |

Os três últimos (AP-13, AP-14 e AP-15) entraram depois da revisão do checkpoint 1. A análise manual tinha problemas reais que o catálogo de 12 não cobria: validação divergente, `priority` como string gerando 500, e cadastro anônimo de `admin`.

### Playbook (18 transformações)

T01 config por ambiente · T02 consulta parametrizada · T03 separar módulo que mistura camadas · T04 hash forte com salt · T05 serialização explícita · T06 regra fora da rota · T07 dependência injetada no lugar de estado global · T08 guard de administração · T09 consulta em lote · T10 handler de erro central · T11 API moderna · T12 constantes nomeadas · T13 logger · T14 nomes descritivos · T15 remover código morto · T16 extrair regra duplicada · T17 validar na borda · T18 configuração segura.

Cada transformação tem antes/depois em **Python e JavaScript** (mais de 70 blocos de código). Algumas trazem detalhes que só apareceram ao testar:
- **T01:** sem segredo, o boot de desenvolvimento usa um valor aleatório e escreve um warning; só falha em `APP_ENV=production`.
- **T03:** traz o adaptador callback → Promise (o `lastID` vem do `this`) e o `asyncHandler` para o Express 4.
- **T10:** em Python, deixa passar os 404/405 do framework.

### Como garanti que a skill é agnóstica

- **Domínio neutro nos exemplos.** O playbook usa faturas, contas e assinaturas, com nomes de campo, status e valores diferentes dos três projetos. Um `grep` por `produto|pedido|usuario|checkout|badCrypto|PAID|blueprint|query.get|usr|eml|…` no `SKILL.md` e nas references volta vazio.
- **Heurísticas por padrão, não por projeto:**
  - stack detectada por manifesto (`requirements.txt`, `package.json`, …) e por import;
  - rotas encontradas por três formas de registro (decorator, registro explícito, módulo de router com prefixo);
  - arquitetura classificada em monolito, camadas parciais ou MVC, com o critério de cada uma.
- **Nenhuma dica externa durante as execuções.** O `CLAUDE.md` da raiz do fork descreve os projetos. Ele foi renomeado para `CLAUDE.md.off` durante todas as execuções headless, para que a skill não recebesse nenhuma informação além do próprio código.
- **Mesma cópia nos 3 projetos.** A skill não foi alterada entre as execuções (`diff -r` vazio nas três cópias).

### Desafios e como resolvi

| Desafio | Solução |
| --- | --- |
| A porta 5000 é do ControlCenter/AirPlay no macOS e responde 403 a tudo. A primeira linha de base do projeto 3 saiu toda 403. | Linha de base refeita na 5001. Na skill, a porta virou configurável (com o default original) e o snapshot confirma com `lsof` que quem responde é a aplicação. |
| O playbook v1 copiava pedaços dos projetos, como `badCrypto` e o domínio de produtos/pedidos. | Reescrito num domínio neutro, verificado por `grep`. |
| T01 v1 derrubava o boot quando não havia `.env`, o que quebra "a aplicação continua funcionando". | Segredo aleatório com warning em desenvolvimento; falha só em produção. |
| O handler central em Python transformava 404/405 do Flask em 500. | O T10 passou a deixar passar as exceções HTTP do framework. |
| O snapshot da Fase 3 ficava sujo por causa do estado do banco (IDs com `AUTOINCREMENT`, rotas destrutivas). | Seed ou backup antes do snapshot; rotas destrutivas por último; restauração antes de validar. |
| A revisão independente (subagentes) achou 10 erros na análise manual e incoerências de severidade na skill. | Tudo corrigido antes da primeira execução (commit `6e97018`). Depois disso, a skill rodou nos 3 projetos **sem precisar de nova iteração**. |
| A execução headless da Fase 3 do projeto 2 morreu duas vezes: o `claude -p` em background era encerrado junto com a sessão que o lançou. | Processo desacoplado (`fork` + `setsid`), retomando a mesma sessão com `--continue`. A skill continuou a partir do código parcial. |
| No modo headless, o `kill` foi negado, e a skill deixou o servidor original no ar (projetos 1 e 3). | A própria skill avisou no final, com os PIDs. Encerrei à mão antes da verificação externa. |

---

## C) Resultados

### Findings por severidade (Fase 2)

| Projeto | Stack detectada | CRITICAL | HIGH | MEDIUM | LOW | Total | Itens da análise manual encontrados |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1: code-smells-project | Python 3.13 + Flask 3.1.1 + sqlite3 | 4 | 4 | 4 | 2 | **14** | 13/13 |
| 2: ecommerce-api-legacy | Node 26 + Express 4.22 + sqlite3 (memória) | 4 | 4 | 3 | 2 | **13** | 11/11 |
| 3: task-manager-api | Python 3.13 + Flask 3.0 + Flask-SQLAlchemy 3.1 | 4 | 3 | 5 | 2 | **14** | 13/13 |

Em cada projeto, conferi uma amostra de 9 a 19 referências `arquivo:linha` contra o código. Todas estavam exatas.

Em todos os três, a skill parou depois da Fase 2 sem tocar em código. O `git status` mostrou só o relatório e o log.

### Estrutura antes e depois

<table>
<tr><th>Projeto</th><th>Antes</th><th>Depois</th></tr>
<tr><td><b>1</b><br>4 arquivos, 780 linhas<br>→ 43 arquivos, 991 linhas</td><td>

```
app.py          rotas + admin + boot
controllers.py  validação + resposta
models.py       SQL + regra (4 domínios)
database.py     conexão global + seed
```

</td><td>

```
app.py         create_app() (composição)
config/        settings.py, regras.py
routes/        6 módulos (só registro)
controllers/   6 controllers
services/      6 services + erros.py
models/        database.py + 4 models
serializers/   produto, usuario, pedido
middlewares/   conexao, erros, admin
utils/         senha.py, tipos.py
```

</td></tr>
<tr><td><b>2</b><br>3 arquivos, 180 linhas<br>→ 27 arquivos, 444 linhas</td><td>

```
src/app.js         boot
src/AppManager.js  schema + seed + rotas
                   + regras (god class)
src/utils.js       config + segredos
                   + cache + "hash"
```

</td><td>

```
src/app.js     main() (composição)
src/config/    settings.js, rules.js
src/models/    db.js (adaptador Promise),
               schema.js + 6 models
src/services/  checkout, payment, report, user
src/controllers/  checkout, report, user
src/routes/    checkout, admin, user
src/middlewares/  asyncHandler, errorHandler,
                  adminGuard
src/errors/    domainErrors.js
src/utils/     password.js, logger.js
```

</td></tr>
<tr><td><b>3</b><br>15 arquivos, 1158 linhas<br>→ 41 arquivos, 1293 linhas</td><td>

```
app.py      boot + SECRET_KEY + debug
models/     task, user, category
routes/     task, user, report (regra + SQL)
services/   notification_service (morto)
utils/      helpers (morto)
seed.py
```

</td><td>

```
app.py         create_app() (composição)
config/        settings.py, rules.py
models/        task, user, category (mantidos)
routes/        task, user, category, report,
               system (só registro)
controllers/   5 controllers + request_body
services/      task, user, category, report,
               stats, persistence, errors
serializers/   task, user, category
middlewares/   errors.py, admin.py
utils/         passwords.py, time.py
```

</td></tr>
</table>

No projeto 3, a skill **não reescreveu** o que já existia. Manteve `models/` e os blueprints, acrescentou as camadas que faltavam e removeu código morto, incluindo duas dependências sem uso do `requirements.txt`.

### Validação externa (fora da skill)

Antes de qualquer refatoração, gravei uma linha de base com o código **original**: [`docs/baseline/before-project-N.json`](docs/baseline/). Ela cobre todas as rotas, com casos de sucesso, 404 e 400. Depois de cada Fase 3, resetei o estado, subi a aplicação refatorada e rodei as mesmas chamadas ([`scripts/smoke.py`](scripts/smoke.py)). Em seguida comparei status e estrutura do corpo ([`scripts/compare.py`](scripts/compare.py)).

| Projeto | Chamadas | Admin desligado (padrão) | Admin ligado + `X-Admin-Token` |
| --- | --- | --- | --- |
| 1 | 35 | 7 divergências, todas intencionais: `/health` sem `secret_key`, `/usuarios` sem `senha`, `POST /produtos` sem corpo 500→400, 3× admin →403 ([diff](docs/runs/project-1/diff.md)) | `/admin/query` 200 com token, 401 sem token; `/admin/reset-db` 200 com token |
| 2 | 7 | 2 divergências, ambas intencionais: relatório e delete →403 ([diff](docs/runs/project-2/diff.md)) | **0 divergências**; o relatório financeiro sai com os mesmos valores ([diff](docs/runs/project-2/diff-admin-on.md)) |
| 3 | 44 | 13 divergências, todas intencionais: 4× sem `password`, 9× delete/relatório →403 ([diff](docs/runs/project-3/diff.md)) | 4 divergências, só a remoção do `password`. Contagens, `completion_rate` e mensagens iguais ([diff](docs/runs/project-3/diff-admin-on.md)) |

Trechos dos logs de boot após a refatoração ([1](docs/runs/project-1/after-server.log), [2](docs/runs/project-2/after-server.log), [3](docs/runs/project-3/after-server.log)):

```
# projeto 1
SECRET_KEY não definida; usando valor aleatório de desenvolvimento
INFO __main__: Servidor iniciado em http://localhost:5001
 * Debug mode: off

# projeto 2
[INFO] Frankenstein LMS rodando na porta 3000...
[INFO] Processando cartão final 4444 para o curso 2     ← antes: número completo + chave do gateway

# projeto 3
SECRET_KEY não definida; usando valor aleatório de desenvolvimento
 * Debug mode: off
 * Running on all addresses (0.0.0.0)
```

A saída completa de cada fase está em [`docs/runs/project-N/`](docs/runs/): `phase-1-2.log` e `phase-3.log`.

### Checklist de validação

| Item | P1 | P2 | P3 |
| --- | --- | --- | --- |
| **Fase 1: Análise** | | | |
| Linguagem detectada corretamente | ✅ Python 3.13 | ✅ JavaScript (Node 26) | ✅ Python 3.13 |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express 4.22.1 | ✅ Flask 3.0.0 + Flask-SQLAlchemy |
| Domínio descrito corretamente | ✅ e-commerce | ✅ LMS com checkout | ✅ task manager |
| Número de arquivos condiz com a realidade | ✅ 4 | ✅ 3 | ✅ 15 |
| **Fase 2: Auditoria** | | | |
| Relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding tem arquivo e linhas exatos | ✅ (amostra de 10) | ✅ (amostra de 9) | ✅ (amostra de 19) |
| Findings ordenados (CRITICAL → LOW) | ✅ | ✅ | ✅ |
| Mínimo de 5 findings | ✅ 14 | ✅ 13 | ✅ 14 |
| APIs deprecated (se aplicável) | ✅ n/a: nenhuma no código | ✅ n/a: nenhuma no código | ✅ `utcnow` + `Query.get` (AP-10) |
| Pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3: Refatoração** | | | |
| Estrutura de diretórios segue MVC | ✅ | ✅ | ✅ |
| Configuração extraída (sem hardcoded) | ✅ `config/settings.py` + `.env.example` | ✅ `src/config/settings.js` + `.env.example` | ✅ `config/settings.py` + `.env.example` |
| Models abstraem os dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ | ✅ | ✅ |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ `middlewares/erros.py` | ✅ `middlewares/errorHandler.js` | ✅ `middlewares/errors.py` |
| Entry point claro | ✅ `create_app()` | ✅ `main()` | ✅ `create_app()` |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem corretamente | ✅ 35 chamadas | ✅ 7 chamadas | ✅ 44 chamadas |

**Anti-patterns que sobraram, segundo a própria skill:**
- **P1 e P3:** as rotas de leitura e escrita comuns continuam sem autenticação, e o token do login do P3 continua falso (AP-07 parcial). Criar autenticação de verdade mudaria o contrato de todos os clientes. A skill deixou isso explícito no box final, com ✗ em "Zero anti-patterns remaining".
- **P2:** a skill marcou zero anti-patterns.

### Comportamento em stacks diferentes

- **Monolito Flask (P1):** separação completa em camadas. O SQL passou a ser parametrizado, a conexão virou uma por requisição e as senhas ganharam scrypt, com migração automática de um banco antigo em texto puro.
- **Express com callbacks (P2):** foi o teste mais forte de agnosticismo, porque não tem `requirements.txt`, usa callbacks e o banco fica em memória. A skill criou um adaptador Promise sobre o driver, usou `asyncHandler` e trocou o N+1 do relatório por um único `LEFT JOIN`. Também tratou casos que o original deixava passar: checkout com e-mail existente e senha errada passou a dar 401; tipo inválido, que derrubava o processo, passou a dar 400.
- **Flask já em camadas (P3):** a skill reconheceu "camadas parciais" e completou o que faltava, sem reescrever do zero. Trocou as APIs deprecated, removeu código morto e fechou o cadastro anônimo de `admin`.
- **Nos três:** a skill listou cada mudança de contrato como intencional e preservou a porta original como default.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.claude.com/en/docs/claude-code) instalado e autenticado (testado com 2.1.x)
- Python 3.12+ (para os projetos 1 e 3) e Node.js 18+ (para o projeto 2)
- Dependências dos projetos:

```bash
cd code-smells-project && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && cd ..
cd task-manager-api   && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && cd ..
cd ecommerce-api-legacy && npm install && cd ..
```

> No macOS, a porta 5000 costuma estar ocupada pelo AirPlay Receiver. Os projetos Flask aceitam `PORT=5001`.

### Executar a skill

Modo interativo (como no enunciado):

```bash
cd code-smells-project      # ou ecommerce-api-legacy / task-manager-api
claude "/refactor-arch"     # Fases 1 e 2; responda "y" para a Fase 3
```

O caminho do relatório pode ser passado como argumento (padrão: `reports/audit-report.md`):

```bash
claude "/refactor-arch ../reports/audit-project-1.md"
```

Modo headless, como foi executado aqui (os logs estão em `docs/runs/`):

```bash
cd code-smells-project
claude -p "/refactor-arch ../reports/audit-project-1.md" --add-dir ../reports \
  --permission-mode acceptEdits --allowedTools "Read Glob Grep Write Edit Bash"      # Fases 1–2 (para na pergunta)
claude -p --continue "sim, prossiga com a Fase 3" --add-dir ../reports \
  --permission-mode acceptEdits --allowedTools "Read Glob Grep Write Edit Bash"      # Fase 3
```

### Validar a refatoração

1. **Resetar o estado** (os IDs da linha de base dependem dele):
   - projeto 1: `rm -f code-smells-project/loja.db`
   - projeto 2: reiniciar o processo (banco em memória)
   - projeto 3: `cd task-manager-api && .venv/bin/python seed.py`
2. **Subir a aplicação:**
   - projeto 1: `PORT=5001 .venv/bin/python app.py`
   - projeto 2: `npm start` (porta 3000)
   - projeto 3: `PORT=5001 .venv/bin/python app.py`
3. **Repetir as chamadas da linha de base e comparar:**

```bash
python3 scripts/smoke.py docs/baseline/requests-project-1.json http://localhost:5001 /tmp/after-1.json
python3 scripts/compare.py docs/baseline/before-project-1.json /tmp/after-1.json
```

O `compare.py` lista as divergências de status e de estrutura do corpo. Elas devem ser **só** as intencionais listadas na seção C. Para testar as rotas de administração, suba com `ENABLE_ADMIN_ROUTES=true ADMIN_TOKEN=<token>` e envie o header `X-Admin-Token`. O `smoke.py` aceita `"headers"` em cada chamada; veja [`docs/runs/project-2/requests-admin-on.json`](docs/runs/project-2/requests-admin-on.json).
