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
| Skill de validação da Fase 3 (somente leitura) | [`code-smells-project/.claude/skills/validate-refactor/`](code-smells-project/.claude/skills/validate-refactor/SKILL.md), copiada nos 3 projetos |
| Diário de execução (decisões, desvios, evidências) | [`docs/HANDOFF.md`](docs/HANDOFF.md) |
| Plano da rodada 2 | [`docs/plano-rodada-2.md`](docs/plano-rodada-2.md) |
| Enunciado original | [`docs/ENUNCIADO.md`](docs/ENUNCIADO.md) |

### Rodada 2: ajustes depois da revisão

A revisão da primeira entrega apontou que a Fase 3 do P1 e do P3 fechava com AP-07 parcial: leituras sensíveis e escritas comuns continuavam sem autenticação, e o box final marcava ✗ em "Zero anti-patterns remaining". A skill mudou em quatro pontos, e os 3 projetos foram refatorados de novo a partir do código original:

- **A Fase 3 só termina sem CRITICAL nem HIGH.** Um passo de pendências (3.6) lista o que sobrou, inclusive sinais do catálogo que o relatório não registrou. Se aparecer CRITICAL ou HIGH, a skill volta ao playbook ou para e pede decisão. "Anti-patterns remaining" só aceita MEDIUM e LOW.
- **O T08 virou "guards de acesso por flag".** Uma fábrica gera três guards: admin (`ENABLE_ADMIN_ROUTES`), leitura sensível (`ENABLE_SENSITIVE_READS`) e escrita (`ENABLE_WRITE_ROUTES`). Com a flag desligada, que é o padrão, a rota responde 403. Ligada, exige `X-Admin-Token`, comparado em tempo constante.
- **Testes antes de refatorar.** Subagentes escrevem testes de caracterização, que passam no código original, e testes do comportamento novo, que falham nele. A refatoração só começa depois disso, e a suíte roda ao fim de cada grupo de transformações.
- **Validação obrigatória.** A skill nova `validate-refactor` confere, sem alterar código, os findings CRITICAL e HIGH, o guard de cada rota, o comportamento com flags desligadas e ligadas, a evidência dos testes e a coerência do box. Sem `VALIDATION PASSED`, o box final não sai.

Os resultados abaixo (seção C) são os da rodada 2. O passo a passo, os incidentes e as decisões estão no [HANDOFF](docs/HANDOFF.md).

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
.claude/skills/
├── refactor-arch/
│   ├── SKILL.md                      orquestração das 3 fases e regras duras (149 linhas)
│   └── references/
│       ├── project-analysis.md       Fase 1: manifestos, imports, banco, rotas, arquitetura, boot/porta/seed
│       ├── anti-patterns-catalog.md  Fase 2: 15 anti-patterns com sinais de detecção e severidade
│       ├── audit-report-template.md  Fase 2: formato exato do relatório
│       ├── mvc-guidelines.md         Fase 3: camadas, responsabilidades, ordem de aplicação, checklist
│       ├── refactoring-playbook.md   Fase 3: 18 transformações com antes/depois em Python e JavaScript
│       └── testing-guidelines.md     Fase 3: framework de teste por stack, isolamento do banco, o que cobrir
└── validate-refactor/
    └── SKILL.md                      checagens C1 a C5, só leitura, chamada no fim da Fase 3
```

Cada uma das 5 áreas de conhecimento obrigatórias tem o seu arquivo. O `testing-guidelines.md` e a `validate-refactor` entraram na rodada 2.

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
- **Testes antes do código (rodada 2).** Com o snapshot gravado, subagentes escrevem os testes por domínio, seguindo o `testing-guidelines.md`. A saída da suíte no código original fica em `suite-original.txt`, e só então a refatoração começa. Teste não pode ser afrouxado para passar: se a precondição mudou por decisão do usuário, a mudança vai para "Intentional changes".
- **Uma ordem única de aplicação**, para que o projeto continue subindo a cada passo. A suíte roda ao fim de cada grupo, com a saída em `suite-grupo-<n>.txt`:
  1. mover para camadas, sem mudar lógica;
  2. segurança: T01, T02, T04, T05, T08, T18;
  3. estrutura: T06, T07, T10, T16, T17;
  4. limpeza: T09, T11–T15.
- **Mudanças de segurança que alteram o contrato são intencionais e documentadas.** As rotas de administração, de leitura sensível e de escrita continuam registradas, mas respondem 403 por padrão. Com a flag do guard ligada, exigem `X-Admin-Token`. Hash de senha deixa de ser devolvido, e as senhas passam a ter hash forte, com o seed recriado com as mesmas senhas de exemplo. Assim dá para validar duas vezes: com as flags desligadas, só as mudanças intencionais divergem; com as flags ligadas e o token, o comportamento original volta.
- **Guard não muda o corpo da requisição.** Exigir a senha do dono numa rota cujo contrato original não envia credencial quebraria todos os clientes. A skill confere a senha só quando o contrato já a envia, como no checkout do P2. Nos outros casos, o guard de escrita é a proteção.
- **Fim da Fase 3 com pendências checadas.** O passo 3.6 junta os findings não resolvidos e os sinais do catálogo achados no código novo. CRITICAL ou HIGH na lista leva de volta ao playbook ou a uma pergunta ao usuário. Depois disso, a skill chama a `validate-refactor` pela ferramenta Skill; uma checagem feita à mão não conta como PASSED.
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

T01 config por ambiente · T02 consulta parametrizada · T03 separar módulo que mistura camadas · T04 hash forte com salt · T05 serialização explícita · T06 regra fora da rota · T07 dependência injetada no lugar de estado global · T08 guards de acesso por flag (admin, leitura sensível, escrita) · T09 consulta em lote · T10 handler de erro central · T11 API moderna · T12 constantes nomeadas · T13 logger · T14 nomes descritivos · T15 remover código morto · T16 extrair regra duplicada · T17 validar na borda · T18 configuração segura.

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
- **Mesma cópia nos 3 projetos.** Na rodada 1, a skill não foi alterada entre as execuções. Na rodada 2, mudou duas vezes depois que P2 e P3 já tinham rodado: o AP-01 ganhou o sinal do seed de usuários que roda em produção, e a regra da conta existente passou a valer só quando o contrato já envia a senha. Nenhuma das duas afeta P2 ou P3. O P2 já tinha a correção do seed, feita em TDD a partir da revisão, e o checkout dele envia a senha. O seed do P3 é um script executado à mão, que o próprio sinal exclui. As três cópias continuam iguais (`diff -r` vazio).

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
| No modo headless, o `kill` foi negado, e a skill deixou o servidor original no ar (projetos 1 e 3). | A própria skill avisou no final, com os PIDs. Encerrei à mão antes da verificação externa. Na rodada 2 isso se repetiu com os servidores de teste, e o tratamento foi o mesmo. |
| Rodada 2: a Fase 3 aceitava fechar com HIGH pendente, desde que listado em "remaining". | Passo 3.6 de pendências, "remaining" restrito a MEDIUM e LOW e a `validate-refactor` como condição para o box. Um subagente revisou a skill procurando caminhos para fechar com HIGH e achou 8 brechas, todas fechadas antes da reexecução. |
| Rodada 2: a revisão do P2 achou um HIGH que a auditoria não registrou: o checkout com e-mail existente não conferia a senha. | Corrigido em TDD e acrescentado ao catálogo como sinal do AP-07. |
| Rodada 2: aplicada ao P1, a regra da conta existente passou a exigir senha no `POST /pedidos`, cujo contrato nunca enviou senha. Com flags ligadas, foram 13 divergências em vez de 4. | A regra foi restrita: a senha só é conferida quando o contrato já a envia; sem isso, o guard de escrita basta. O P1 reverteu a exigência em TDD. |
| Rodada 2: a revisão do P1 achou um pedido parcial gravado em erro 500 e lacunas de teste de guard que a `validate-refactor` deixou passar. Também achou o relatório de vendas na flag de leitura sensível, enquanto o T08 manda relatório para administração. | Corrigido em TDD no P1. Na skill, o T10 passou a exigir rollback no handler de 500, a regra do relatório foi desempatada (administração) e a C4 da `validate-refactor` passou a cobrar os testes de guard e de transação. A C5 também confere a documentação do projeto. |
| Rodada 2: o limite de uso interrompeu as execuções headless várias vezes. Em uma delas, o P3 ficou com código de produção escrito enquanto os testes ainda rodavam. | Retomada com `--continue` quando o estado estava consistente. Quando não estava, o projeto voltou ao código original e a Fase 3 rodou do zero. |

---

## C) Resultados

### Findings por severidade (Fase 2)

| Projeto | Stack detectada | CRITICAL | HIGH | MEDIUM | LOW | Total | Itens da análise manual encontrados |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1: code-smells-project | Python 3.13 + Flask 3.1.1 + sqlite3 | 5 | 4 | 4 | 2 | **15** | 13/13 |
| 2: ecommerce-api-legacy | Node 24 + Express 4.22 + sqlite3 (memória) | 5 | 4 | 3 | 2 | **14** | 11/11 |
| 3: task-manager-api | Python 3.13 + Flask 3.0 + Flask-SQLAlchemy 3.1 | 5 | 3 | 5 | 2 | **15** | 13/13 |

Cada projeto tem um finding a mais que na rodada 1. No P1 e no P3, a auditoria nova registrou um AP-03 (módulo que mistura dados, regra e roteamento) que a primeira não tinha marcado. No P2, o AP-07 CRITICAL foi dividido em dois, um para o relatório financeiro e outro para o `DELETE`, e o checkout entrou como HIGH de escrita sem autenticação.

Na rodada 1, conferi uma amostra de 9 a 19 referências `arquivo:linha` por projeto contra o código, e todas estavam exatas.

Nos três projetos, a skill parou depois da Fase 2 sem tocar em código. O `git status` mostrou só o relatório e o log.

### Estrutura antes e depois

<table>
<tr><th>Projeto</th><th>Antes</th><th>Depois</th></tr>
<tr><td><b>1</b><br>4 arquivos, 780 linhas<br>→ 41 arquivos, 1099 linhas<br>+ 174 testes</td><td>

```
app.py          rotas + admin + boot
controllers.py  validação + resposta
models.py       SQL + regra (4 domínios)
database.py     conexão global + seed
```

</td><td>

```
app.py         composição + boot
config/        settings.py, regras.py
routes/        6 módulos (registro + guard)
controllers/   6 controllers + validadores
services/      6 services + erros.py
models/        database.py + 5 models
serializers/   usuario (sem senha)
middlewares/   erros, guards
utils/         senha.py
tests/         conftest + 4 domínios
```

</td></tr>
<tr><td><b>2</b><br>3 arquivos, 180 linhas<br>→ 24 arquivos, 360 linhas<br>+ 80 testes</td><td>

```
src/app.js         boot
src/AppManager.js  schema + seed + rotas
                   + regras (god class)
src/utils.js       config + segredos
                   + cache + "hash"
```

</td><td>

```
src/app.js     composição + boot
src/config/    settings.js, rules.js
src/models/    database.js (adaptador Promise),
               schema.js + 6 models
src/services/  checkout, report, user
src/controllers/  checkout, report, user
src/routes/    index.js (registro + guard)
src/middlewares/  asyncHandler, errorHandler,
                  guards
src/errors/    domainError.js
src/utils/     password.js, logger.js
tests/         integração + unit/
```

</td></tr>
<tr><td><b>3</b><br>15 arquivos, 1158 linhas<br>→ 39 arquivos, 1324 linhas<br>+ 195 testes</td><td>

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
database.py    instância do SQLAlchemy
config/        settings.py, rules.py
models/        task, user, category (mantidos)
routes/        task, user, category, report,
               system (registro + guard)
controllers/   5 controllers + request_body
services/      task, user, category, report,
               errors
serializers/   task, user, category
middlewares/   errors.py, guards.py
utils/         passwords.py, time.py
tests/         conftest + 7 módulos
```

</td></tr>
</table>

No projeto 3, a skill **não reescreveu** o que já existia. Manteve `models/` e os blueprints, acrescentou as camadas que faltavam e removeu código morto.

### Testes escritos antes da refatoração

| Projeto | Suíte | No código original | No fim da Fase 3 |
| --- | --- | --- | --- |
| 1 | `pytest`, 174 testes | 101 escritos antes: 49 verdes, 52 vermelhos. Outros 4 vieram nas correções da validação e 69 na revisão; dos 69, os 6 que cobrem uma correção ficaram vermelhos antes do código | 174/174 |
| 2 | `npm test` (`node --test`), 80 testes | 38 escritos antes; os demais cobrem as camadas novas e as correções da revisão | 80/80 |
| 3 | `pytest`, 195 testes | 174 escritos antes (110 de caracterização, 64 de comportamento novo) | 195/195 |

Os testes acrescentados depois da Fase 3 vieram da revisão por subagentes: flag isolada por rota (cada flag ligada sozinha libera só as rotas dela), token errado, defesa de papel testada direto no serviço e, no P1, falha no meio de um pedido, que precisa terminar sem nada gravado. A saída da suíte depois de cada grupo de transformações ficou no diretório de trabalho da skill, e a `validate-refactor` a conferiu (checagem C4).

### Validação externa (fora da skill)

Antes de qualquer refatoração, gravei uma linha de base com o código **original**: [`docs/baseline/before-project-N.json`](docs/baseline/). Ela cobre todas as rotas, com casos de sucesso, 404 e 400. Depois de cada Fase 3, resetei o estado, subi a aplicação refatorada e rodei as mesmas chamadas ([`scripts/smoke.py`](scripts/smoke.py)). Em seguida comparei status e estrutura do corpo ([`scripts/compare.py`](scripts/compare.py)). A variante com flags ligadas usa as mesmas chamadas com `X-Admin-Token` em todas ([`scripts/with-token.py`](scripts/with-token.py)).

| Projeto | Chamadas | Flags desligadas (padrão) | Flags ligadas + `X-Admin-Token` |
| --- | --- | --- | --- |
| 1 | 35 | 26 divergências, todas intencionais: 25 chamadas a rotas guardadas →403 e `/health` sem `secret_key` ([diff](docs/runs/project-1/diff.md)) | 4 divergências, só mudanças de segurança já documentadas: `/health` sem `secret_key`, `/usuarios` e `/usuarios/<id>` sem `senha`, `POST /produtos` sem corpo 500→400 ([diff](docs/runs/project-1/diff-flags-on.md)) |
| 2 | 7 | 7 divergências, todas →403: checkout (escrita), relatório financeiro e `DELETE` (admin) ([diff](docs/runs/project-2/diff.md)) | **0 divergências**; o relatório financeiro sai com os mesmos valores ([diff](docs/runs/project-2/diff-flags-on.md)) |
| 3 | 44 | 31 divergências, todas intencionais: 30 →403 e o login sem `password` ([diff](docs/runs/project-3/diff.md)) | 4 divergências, só a remoção do `password`. Contagens, `completion_rate` e mensagens iguais ([diff](docs/runs/project-3/diff-flags-on.md)) |

Com as flags desligadas, as divergências cresceram em relação à rodada 1 porque leitura sensível e escrita agora também respondem 403. Com as flags ligadas, o comportamento original volta, menos as mudanças de segurança que já estavam documentadas.

Trechos dos logs de boot após a refatoração ([1](docs/runs/project-1/after-server.log), [2](docs/runs/project-2/after-flags-on-server.log), [3](docs/runs/project-3/after-server.log)):

```
# projeto 1
SECRET_KEY não definida; usando valor aleatório de desenvolvimento
 * Debug mode: off

# projeto 2 (flags ligadas, para o checkout rodar)
2026-10-23T00:16:12.005Z INFO Frankenstein LMS rodando na porta 3000...
2026-10-23T00:16:19.324Z INFO Pagamento processado {"userId":2,"courseId":2,"card":"****4444","status":"PAID"}
                         ← antes: número completo do cartão + chave do gateway

# projeto 3
SECRET_KEY não definida; usando valor aleatório de desenvolvimento
 * Debug mode: off
 * Running on all addresses (0.0.0.0)
```

A saída completa de cada fase está em [`docs/runs/project-N/`](docs/runs/): `phase-1-2.log` e `phase-3.log`. No P1, as retomadas da Fase 3 estão em `phase-3a.log` a `phase-3c.log`.

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
| Mínimo de 5 findings | ✅ 15 | ✅ 14 | ✅ 15 |
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
| Testes escritos antes da refatoração, todos verdes no fim | ✅ 174/174 | ✅ 80/80 | ✅ 195/195 |
| Rotas sem autenticação atrás de um guard T08 | ✅ 13 de 19 | ✅ 3 de 3 | ✅ 13 de 22 |
| Zero CRITICAL/HIGH restante (`validate-refactor`) | ✅ PASSED | ✅ PASSED | ✅ PASSED |

Ficaram sem guard o login, `/health`, a raiz e as leituras sem dado pessoal ou financeiro: produtos e busca no P1; tarefas, busca, estatísticas, categorias e tarefas de um usuário no P3.

**Anti-patterns que sobraram, segundo a própria skill (só MEDIUM e LOW):**
- **P1:** AP-08 (MEDIUM), porque `criar_pedido` consulta o produto duas vezes por item; AP-11 (LOW), com o status `'pendente'` como literal SQL e a versão repetida; AP-12 (LOW), com o parâmetro `id` e o banner de boot em `print`.
- **P2:** dois MEDIUM. O `DELETE /api/users/:id` responde 200 para id inexistente e não apaga matrículas nem pagamentos, e o checkout não roda numa transação: com o cartão recusado, o usuário novo continua criado, como no original. Os dois pedem uma decisão de produto.
- **P3:** três LOW. Dependências sem uso no `requirements.txt`, alguns literais de status e mensagens inline, e `print` no `seed.py`, que é um script de linha de comando.

**Preservado de propósito e documentado no box:** o `POST /admin/query` do P1 continua executando o SQL do corpo, agora atrás de `ENABLE_ADMIN_ROUTES` e do token. O `/login` do P1 continua sem guard e sem devolver token, e o do P3 continua devolvendo `fake-jwt-token-<id>`, que nenhuma rota verifica. Em ambos, a proteção vem dos guards das rotas.

### Comportamento em stacks diferentes

- **Monolito Flask (P1):** separação completa em camadas. O SQL passou a ser parametrizado, a conexão virou uma por requisição e as senhas ganharam scrypt. Um `loja.db` da versão antiga precisa ser recriado. O seed de usuários de exemplo só roda fora de produção, e o cadastro de usuário (`POST /usuarios`) passou para trás do guard de escrita, por decisão minha durante a Fase 3. A revisão achou um pedido parcial gravado quando o serviço falhava no meio: o handler de 500 tratava a exceção e o fim da requisição fazia commit. O handler agora desfaz a transação, com teste.
- **Express com callbacks (P2):** foi o teste mais forte de agnosticismo, porque não tem `requirements.txt`, usa callbacks e o banco fica em memória. A skill criou um adaptador Promise sobre o driver, usou `asyncHandler` e trocou o N+1 do relatório por um único `LEFT JOIN`. Também tratou casos que o original deixava passar: tipo inválido, que derrubava o processo, passou a dar 400. O checkout com e-mail existente e senha errada passou a dar 401 numa correção em TDD depois da revisão, porque a Fase 3 não tinha pegado esse caso.
- **Flask já em camadas (P3):** a skill reconheceu "camadas parciais" e completou o que faltava, sem reescrever do zero. Trocou as APIs deprecated, removeu código morto e fechou o cadastro anônimo de `admin`.
- **Nos três:** a skill listou cada mudança de contrato como intencional e preservou a porta original como default. O mesmo guard T08 foi implementado em Python (`exigir_flag`, com `hmac.compare_digest`) e em JavaScript (`exigirFlag`, com `crypto.timingSafeEqual`).

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
  --permission-mode acceptEdits --allowedTools "Read Glob Grep Write Edit Bash Agent Skill"   # Fases 1–2 (para na pergunta)
claude -p --continue "sim, prossiga com a Fase 3" --add-dir ../reports \
  --permission-mode acceptEdits --allowedTools "Read Glob Grep Write Edit Bash Agent Skill"   # Fase 3
```

`Agent` é necessário para os subagentes que escrevem os testes, e `Skill` para a chamada da `validate-refactor`. O [`scripts/run-skill.sh`](scripts/run-skill.sh) faz as duas chamadas e grava os logs: `scripts/run-skill.sh code-smells-project ../reports/audit-project-1.md "$PWD/docs/runs/project-1"`.

### Rodar os testes

```bash
cd code-smells-project && .venv/bin/python -m pytest -q tests     # P1
cd ecommerce-api-legacy && npm test                                # P2
cd task-manager-api && .venv/bin/python -m pytest -q tests         # P3
```

No P1, o pytest está no `requirements-dev.txt` (`.venv/bin/pip install -r requirements-dev.txt`). O P3 não tem esse arquivo; instale com `.venv/bin/pip install pytest`.

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

O `compare.py` lista as divergências de status e de estrutura do corpo. Elas devem ser **só** as intencionais listadas na seção C.

4. **Repetir com as flags ligadas e o token:**

```bash
python3 scripts/with-token.py docs/baseline/requests-project-1.json tok123 /tmp/requests-on.json
# reinicie o estado e suba a aplicação com:
# ENABLE_ADMIN_ROUTES=true ENABLE_SENSITIVE_READS=true ENABLE_WRITE_ROUTES=true ADMIN_TOKEN=tok123
python3 scripts/smoke.py /tmp/requests-on.json http://localhost:5001 /tmp/after-1-on.json
python3 scripts/compare.py docs/baseline/before-project-1.json /tmp/after-1-on.json
```

Com as flags ligadas, só podem sobrar as mudanças de segurança da coluna "flags ligadas" da seção C. As listas de chamadas usadas aqui estão em `docs/runs/project-N/requests-flags-on.json`.
