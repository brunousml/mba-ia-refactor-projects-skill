# Handoff: Desafio 4 (skill `refactor-arch`)

Atualizado ao fim de cada etapa. O plano do desafio e o plano de execução ficam no repositório de planejamento, fora
deste fork.

## Estado atual

Rodada 2 em andamento, seguindo o [plano da rodada 2](plano-rodada-2.md). Na plataforma, o status é "Revisão necessária, ajustando".

A revisão da entrega apontou que a Fase 3 do P1 e do P3 terminava com AP-07 parcial: leituras sensíveis e escritas continuavam sem autenticação, e o box marcava ✗ em "Zero anti-patterns remaining". Endureci a skill e estou refazendo os 3 projetos a partir do código original, com TDD.

| Etapa | Status | Artefato |
|---|---|---|
| Skill: a Fase 3 não fecha com CRITICAL/HIGH | Feito | `refactor-arch/SKILL.md` (3.6 Pendências, 3.7 Saída) |
| T08 com 3 guards por flag | Feito | `references/refactoring-playbook.md` (T08), `anti-patterns-catalog.md` (AP-07) |
| TDD na Fase 3, com testes escritos por subagentes Sonnet | Feito | `SKILL.md` 3.2, `references/testing-guidelines.md` |
| Skill `validate-refactor` (C1 a C5) | Feito | `.claude/skills/validate-refactor/SKILL.md` |
| Revisão da skill por subagente | 8 brechas, todas fechadas | seção "Revisão por subagentes" |
| P2 | Refeito, revisado e commitado | [relatório](../reports/audit-project-2.md), [log 3](runs/project-2/phase-3.log), [diff off](runs/project-2/diff.md), [diff on](runs/project-2/diff-flags-on.md) |
| P3 | Refeito, verificado e commitado; revisão por subagente em andamento | [relatório](../reports/audit-project-3.md), [log 3](runs/project-3/phase-3.log), [diff off](runs/project-3/diff.md), [diff on](runs/project-3/diff-flags-on.md) |
| P1 | Rodando de novo com a skill atual (a versão commitada usou a skill de antes das correções) | [log 1–2](runs/project-1/phase-1-2.log) |
| README e reenvio da URL | Pendente; o reenvio é feito pelo usuário | |

## O que mudou na skill

As 3 cópias de `.claude/skills/` (refactor-arch e validate-refactor) estão idênticas (`diff -r` vazio).

A Fase 3 só fecha sem CRITICAL ou HIGH (passo 3.6). A lista de pendências junta os findings do relatório, os sinais do catálogo achados no código novo (mesmo os que o relatório não registrou), os testes vermelhos e os ✗ do checklist. Com CRITICAL ou HIGH na lista, a skill volta ao playbook ou para e pede uma decisão. Se o usuário aceitar o risco, o box marca ✗; "Anti-patterns remaining" só aceita MEDIUM e LOW.

O T08 virou "guards de acesso por flag". Uma fábrica gera três guards:

- `ENABLE_ADMIN_ROUTES`: reset, SQL, relatório e exclusão em massa;
- `ENABLE_SENSITIVE_READS`: dados pessoais ou financeiros;
- `ENABLE_WRITE_ROUTES`: POST, PUT, PATCH e DELETE comuns.

Com a flag desligada, a rota responde 403. Ligada, exige `X-Admin-Token` comparado em tempo constante e responde 401 sem ele. Quando a rota reaproveita uma conta existente identificada pelo corpo da requisição, a senha também precisa ser conferida.

Os testes vêm antes de qualquer mudança no código de produção (passo 3.2). Subagentes em paralelo, um por domínio e com `model: "sonnet"`, escrevem testes de caracterização, verdes no original e feitos pela interface HTTP, e testes de comportamento novo, vermelhos no original. A refatoração só começa depois que todos terminam e o `suite-original.txt` é gravado. Cada serviço ou model novo nasce com o teste unitário antes do código. A suíte roda depois de cada grupo de transformações, e a saída fica em `suite-grupo-1..4.txt` no diretório de trabalho.

A `validate-refactor` é somente leitura e confere cinco coisas: se os CRITICAL e HIGH foram resolvidos, com varredura do catálogo inteiro (C1); se cada rota tem o guard certo (C2); o comportamento com flags off e on (C3); a evidência dos testes (C4); e se o box bate com as checagens (C5). Ela precisa ser chamada pela ferramenta Skill, porque aplicar as checagens à mão não conta como PASSED.

O box de saída ganhou a linha de testes, com a contagem antes e depois. "Intentional changes" agora inclui o comportamento arriscado que ficou de propósito.

## Revisão por subagentes

| Revisor | Achados | O que foi feito |
|---|---|---|
| Skill | 8 brechas. As mais graves: a validate-refactor podia ser simulada à mão, a suíte por grupo não deixava evidência e o diretório de trabalho não chegava à validate-refactor | Todas fechadas no commit `fix(skill): fecha brechas da revisão…` |
| P1 (versão feita com a skill anterior) | Nenhum CRITICAL ou HIGH. 3 LOW: token errado testado só no admin, comportamento preservado fora do box, grupos não validados um a um | Os três viraram regras da skill (testing-guidelines e box). O P1 está sendo refeito |
| P2 | Um HIGH que a nova auditoria não registrou: o checkout reaproveitava a conta pelo e-mail sem conferir a senha. Um MEDIUM: faltava teste com token errado | O catálogo (AP-07) e o T08 passaram a cobrir o sinal. Corrigi o código em TDD, com os testes vermelhos primeiro |
| P3 | Em andamento (Opus, por ser revisão de segurança) | |

## Resultados por projeto

| Projeto | Testes | Flags off | Flags on + token | Observação |
|---|---|---|---|---|
| P2 | `npm test` 70/70; 38 escritos antes da refatoração, o resto são unitários das camadas novas e da correção do checkout | 7 divergências, todas 403 intencionais | 0 divergências | validate-refactor PASSED. Ficam 2 MEDIUM: DELETE de id inexistente responde 200, e o checkout não roda em transação |
| P3 | `pytest` 184/184; 174 escritos antes (110 de caracterização, 64 de comportamento novo) | 31 divergências: 30 são 403 e uma é o login sem `password` | 4, todas a remoção de `password`; os valores conferidos batem com o original | validate-refactor PASSED, com evidência em todos os grupos. 13 de 22 rotas guardadas. Ficam 3 LOW |
| P1 | Rodando | | | A versão anterior teve 129/129 testes e 13 rotas guardadas |

Ferramentas novas:

- `scripts/run-skill.sh` roda as Fases 1 a 3 em modo headless, e `scripts/run-phase3.sh` retoma só a Fase 3;
- `scripts/with-token.py` gera a variante "flags on" das chamadas, com `X-Admin-Token` em todas.

Variáveis da validação com flags on:

```bash
ENABLE_ADMIN_ROUTES=true ENABLE_SENSITIVE_READS=true ENABLE_WRITE_ROUTES=true ADMIN_TOKEN=tok123
```

## Incidentes

O limite de uso interrompeu as execuções headless 4 vezes. Quando a sessão parou num ponto limpo, retomei com `--continue`. Quando o estado ficou inconsistente, recomecei do código original. Foi o caso do P3: apareceu código de produção enquanto os subagentes de teste ainda rodavam, e os `.py` dos testes sumiram. Daí veio a regra de esperar todos os subagentes antes de refatorar.

Um commit do P2 levou junto o estado intermediário do P1, que estava no índice desde o `git checkout <commit>^ -- <projeto>`. Desfiz e refiz o commit antes de qualquer push. Depois de restaurar um projeto com `git checkout`, rode `git reset -q HEAD -- <projeto>` e faça commit com `git add <caminhos>`, nunca com `-A`.

`node --test tests/` falha no Node 24. A `testing-guidelines.md` passou a usar `node --test 'tests/**/*.test.js'`, chamado por `npm test`.

A config global do git estava com outra identidade. A global e a local agora usam `Bruno Melo <brunousml@gmail.com>`, e os 7 commits locais da rodada 2 foram reescritos com `commit-tree`, sem mudar árvore, mensagens ou datas.

Nas primeiras execuções, o agente aplicava os 4 grupos de uma vez com a justificativa de que o projeto era pequeno. A skill agora proíbe isso e exige um `suite-grupo-<n>.txt` por grupo.

## Próximo passo

1. Quando o P1 terminar: verificação externa (pytest, `smoke.py` e `compare.py` com flags off e on), checagem de pendências e commit.
2. Revisão do novo P1 por subagente. Corrigir em TDD o que a revisão do P1 e a do P3 apontarem.
3. Atualizar o README (tabelas de validação, mudanças intencionais, a ressalva de AP-07 parcial e o checklist) e este handoff, passando os textos pelo humanizer.
4. Commits por etapa e push, com confirmação do usuário.
5. O usuário reenvia a URL na plataforma.

---

# Histórico: Rodada 1 (entrega original)

> Os logs, `after*.json` e diffs citados abaixo foram substituídos pelos da rodada 2, e os `*-admin-on*` viraram
> `*-flags-on*`. As versões da rodada 1 estão no commit `ed3a7d1` (`git show ed3a7d1:docs/runs/project-N/<arquivo>`).

## Linha de base

Cada `requests-project-N.json` lista as chamadas. Cada `before-project-N.json` guarda o status e o corpo gravados no
código **original**.

| Projeto         | Chamadas | Porta | Status observados            | Arquivos                                                                                                                          |
|-----------------|----------|-------|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| 1 (Flask)       | 35       | 5001  | 200, 201, 400, 401, 404, 500 | [requests](baseline/requests-project-1.json), [before](baseline/before-project-1.json), [log](runs/project-1/baseline-server.log) |
| 2 (Express)     | 7        | 3000  | 200, 400, 404                | [requests](baseline/requests-project-2.json), [before](baseline/before-project-2.json), [log](runs/project-2/baseline-server.log) |
| 3 (Flask + ORM) | 44       | 5001  | 200, 201, 400, 401, 404, 409 | [requests](baseline/requests-project-3.json), [before](baseline/before-project-3.json), [log](runs/project-3/baseline-server.log) |

Ferramentas:

- [`scripts/smoke.py`](../scripts/smoke.py) executa as chamadas.
- [`scripts/compare.py`](../scripts/compare.py) compara status e estrutura do corpo. Com `--valores`, compara também os
  campos indicados.

### Como reproduzir (estado inicial obrigatório)

Os IDs das chamadas dependem do estado inicial do banco. Antes de cada execução, faça o reset e suba o servidor:

| Projeto | Reset                                                                                   | Subir                                                                       |
|---------|-----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| 1       | `rm -f code-smells-project/loja.db` (o `AUTOINCREMENT` não volta com `DELETE`)          | `cd code-smells-project && .venv/bin/python -m flask --app app run -p 5001` |
| 2       | Reiniciar o processo (banco em memória)                                                 | `cd ecommerce-api-legacy && npm start`                                      |
| 3       | `cd task-manager-api && .venv/bin/python seed.py` (o banco fica em `instance/tasks.db`) | `cd task-manager-api && .venv/bin/python -m flask --app app run -p 5001`    |

```bash
python3 scripts/smoke.py docs/baseline/requests-project-1.json http://localhost:5001 /tmp/after-1.json
python3 scripts/compare.py docs/baseline/before-project-1.json /tmp/after-1.json
```

## Revisão do checkpoint 1

Três subagentes revisaram, cada um, uma parte do trabalho. Itens corrigidos:

- **Análise manual.** 10 itens estavam com linha, descrição ou severidade errada. Exemplos:
    - a SQL injection do P1 citava linhas protegidas pelo conversor `<int:>`;
    - no P3, o `GET /users` não vaza o hash. As rotas que vazam são outras quatro;
    - `datetime` é usado no `app.py` do P3.

  Também entraram 6 problemas que faltavam, como o cadastro anônimo de `admin` no P3, classificado como CRITICAL. Foi
  adicionada a coluna AP, que liga cada item ao catálogo.
- **Skill:**
    - Catálogo: de 12 para 15 anti-patterns (duplicação, validação ausente, configuração insegura). A regra de
      severidade deixou de ser contraditória, e a Fase 2 passou a ser só leitura.
    - Playbook: de 15 para 18 transformações. Agora usa um domínio neutro, para não copiar código dos projetos. O T01
      não derruba mais o boot sem `.env`. Entraram o adaptador callback → promise, o `asyncHandler`, um handler de erro
      que preserva 404/405 e um hash que não gera 500 com formato inválido.
    - `SKILL.md`: frontmatter YAML válido. O snapshot passou a usar reset de estado, diretório temporário fora do
      projeto e verificação de porta. Ficou uma ordem única de aplicação, e o checklist MVC do enunciado entrou na saída
      da Fase 3.
- **Scripts:**
    - `compare.py` agora trata erro de conexão como divergência, une os tipos de todos os itens de uma lista, considera
      `int` e `float` como "número", recusa IDs duplicados e aceita `--valores`.
    - `smoke.py` captura timeout e queda de conexão.

## Decisões e desvios

- **Porta 5000 ocupada no macOS (ControlCenter/AirPlay).** A primeira linha de base do P3 subiu na 5000 e recebeu 403 em
  tudo. Foi descartada e refeita na 5001.
- **A linha de base do Flask rodou com `flask run`, com debug desligado.** O original roda com `python app.py`, com
  debug ligado. As respostas não mudam, porque todos os handlers capturam as exceções. A diferença fica registrada.
- **Comportamentos ruins preservados na linha de base.** A Fase 3 deve mudá-los de propósito:
    - `POST /produtos` sem corpo devolve 500 (P1).
    - O checkout cria o usuário antes de validar o pagamento (P2).
    - `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `/login` devolvem o hash da senha (P3).
    - `/health` devolve a `secret_key` (P1).
- **O log de baseline do P2 contém o número de cartão de teste (`4111…`)** e a chave fictícia do gateway. O próprio
  código original os imprime (`AppManager.js:45`). São dados de teste do `api.http`, não dados reais.
- **Node 26.7:** o `sqlite3@5.1.6` compilou sem precisar do plano B.
- **O `CLAUDE.md` da raiz do fork está no `.gitignore`.** Durante as execuções headless ele vira `CLAUDE.md.off`, para a
  skill não receber informação sobre os projetos.
- **Comando headless:** `--add-dir ../reports`, porque o relatório é gravado fora do diretório do projeto.

## Projeto 1: resultado das Fases 1–2

Comando:
`claude -p "/refactor-arch ../reports/audit-project-1.md" --add-dir ../reports --permission-mode acceptEdits --allowedTools "Read Glob Grep Write Edit Bash"`,
rodado em `code-smells-project/` com o `CLAUDE.md` da raiz renomeado para `.off`.

| Critério                    | Resultado                                                                                                                |
|-----------------------------|--------------------------------------------------------------------------------------------------------------------------|
| Stack detectada             | Python 3.13 (versão do `.venv`) + Flask 3.1.1, flask-cors 5.0.1, sqlite3                                                 |
| Domínio                     | E-commerce (produtos, usuários e login, pedidos com estoque, relatório de vendas)                                        |
| Arquivos                    | 4 (`app.py`, `controllers.py`, `database.py`, `models.py`), ~780 linhas                                                  |
| Rotas inventariadas         | 19, o mesmo total da linha de base                                                                                       |
| Findings                    | 14: CRITICAL 4, HIGH 4, MEDIUM 4, LOW 2                                                                                  |
| Cobertura da análise manual | 13 de 13 itens encontrados                                                                                               |
| Linhas                      | Amostra de 10 referências conferida contra o código: todas exatas                                                        |
| Pausa                       | Terminou em `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`. O `git status` mostrou só o relatório e o log |

Divergências em relação à análise manual (decisões da skill, não erros):

- Classificou a arquitetura como "camadas parciais", e não como monolito, porque já existem `models.py` e
  `controllers.py`.
- Não marcou AP-03 (god module), porque nenhum arquivo junta as três responsabilidades. Pelo catálogo, esse caso vira
  AP-05, o mesmo critério da análise manual.
- Não encontrou API deprecated no projeto 1. Isso está correto, porque o projeto 1 não usa nenhuma.

## Projeto 1: resultado da Fase 3

Comando:
`claude -p --continue "sim, prossiga com a Fase 3" --add-dir ../reports --permission-mode acceptEdits --allowedTools "Read Glob Grep Write Edit Bash"`,
em `code-smells-project/`. A saída está em [`runs/project-1/phase-3.log`](runs/project-1/phase-3.log).

Estrutura nova: `app.py` (composição), `config/`, `routes/`, `controllers/`, `services/`, `models/`, `serializers/`,
`middlewares/`, `utils/` e `.env.example`. Os 4 arquivos originais saíram. O checklist MVC da skill ficou com ✓ em todos
os itens. "Zero anti-patterns remaining" ficou com ✗, justificado pelo AP-07: o projeto não tem autenticação real, e
criar uma quebraria o contrato. O CORS `*` é configurável.

**Verificação externa** (`rm -f loja.db`, `PORT=5001 python app.py`, `smoke.py` e `compare.py`): 35 chamadas, 7
divergências, todas intencionais ([diff](runs/project-1/diff.md)).

| Chamada                                                   | Antes → depois | Motivo                                                     |
|-----------------------------------------------------------|----------------|------------------------------------------------------------|
| `health`                                                  | formato        | saem `secret_key`, `db_path` e `debug` (nenhum campo novo) |
| `usuarios-listar`, `usuarios-detalhe-ok`                  | formato        | sai `senha` (nenhum campo novo)                            |
| `produtos-criar-400-sem-body`                             | 500 → 400      | validação na borda                                         |
| `admin-query-select`, `admin-query-400`, `admin-reset-db` | 200/400 → 403  | admin desligado por padrão                                 |

Checagens manuais extras:

- Com `ENABLE_ADMIN_ROUTES=true ADMIN_TOKEN=…`: `/admin/query` sem token retorna 401, com token retorna 200
  (`COUNT(*) = 10`). `/admin/reset-db` com token retorna 200.
- `POST /login` com `admin@loja.com`/`admin123` retorna 200, com a senha agora em scrypt.
- Nenhum SQL concatenado com valor do cliente sobrou. Os dois f-strings restantes montam só nomes fixos de tabela e
  marcadores `?`. Não há `print`, e o log do servidor não tem erro.

Observações:

- A skill deixou o app original rodando na porta 5050, porque o `kill` foi negado no modo headless. Encerrei os
  processos à mão. Nos próximos projetos, conferir com `lsof` depois da Fase 3.
- A skill também atualizou o `README.md` do projeto (estrutura, configuração e rotas de admin).
- O material de trabalho da skill ficou em um diretório temporário fora do repositório, como pede o `SKILL.md`.

## Projeto 2: resultado das Fases 1–2

Mesmo comando, em `ecommerce-api-legacy/`, com a skill copiada sem alteração (`diff -r` vazio).

| Critério            | Resultado                                                                                                                                  |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| Stack detectada     | JavaScript (Node 26.7) + Express 4.22.1, sqlite3 5.1.7 em memória                                                                          |
| Domínio             | LMS com checkout (cursos, matrícula, pagamento, relatório financeiro)                                                                      |
| Arquitetura         | Monolito (`AppManager.js` junta schema, seed, regras e rotas)                                                                              |
| Rotas inventariadas | 3 (`POST /api/checkout`, `GET /api/admin/financial-report`, `DELETE /api/users/:id`)                                                       |
| Findings            | 13: CRITICAL 4, HIGH 4, MEDIUM 3, LOW 2                                                                                                    |
| Linhas              | Amostra conferida (`utils.js:2-5`, `17-23`; `AppManager.js:18`, `45`, `68`, `92`, `104`, `106`, `131-136`): todas exatas                   |
| Pausa               | Terminou em `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`. O `git status` mostrou só o relatório, o log e a cópia da skill |

Em relação à análise manual:

- Todos os itens das tabelas foram encontrados. A skill marcou AP-03 (god class) como CRITICAL, assim como a análise
  manual.
- A skill encontrou ainda a senha em texto puro no seed (`AppManager.js:18`).
- Ficou implícito que o checkout cria o usuário **antes** de validar o pagamento. O relatório cobre o fluxo pelo AP-05,
  mas não cita isso como problema à parte.
- Não marcou AP-02 (todas as queries usam `?`) nem AP-10. Isso está correto.

## Projeto 2: resultado da Fase 3

A estrutura nova fica em `src/`: `app.js` (composição), `config/`, `models/` (adaptador Promise sobre o driver de
callback, com um model por tabela), `services/`, `controllers/`, `routes/`, `middlewares/` (`asyncHandler`,
`errorHandler`, `adminGuard`), `errors/`, `utils/` e `.env.example`. `AppManager.js` e `utils.js` foram removidos. A
skill marcou ✓ em todo o checklist, inclusive em "Zero anti-patterns remaining".

**Execução interrompida duas vezes.** O `claude -p` rodava como job em background desta sessão e morreu junto com ela:
na 1ª vez logo depois do snapshot, na 2ª no meio da refatoração. A 3ª execução rodou desacoplada (`fork` + `setsid`) e
retomou a mesma sessão com `--continue`, partindo do código parcial e do snapshot.
O [log da Fase 3](runs/project-2/phase-3.log) registra só essa última execução. No projeto 3, a execução foi desacoplada
desde o início.

**Verificação externa** (`node src/app.js`, porta 3000, banco em memória, `smoke.py` e `compare.py`):

| Execução                                     | Divergências                                                                       | Arquivos                                                                                                                                |
|----------------------------------------------|------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| Padrão (admin desligado)                     | 2, intencionais: `relatorio-financeiro` e `usuario-deletar` passam de 200 para 403 | [after](runs/project-2/after.json), [diff](runs/project-2/diff.md), [server](runs/project-2/after-server.log)                           |
| `ENABLE_ADMIN_ROUTES=true` + `X-Admin-Token` | 0. O relatório saiu com os mesmos valores do original                              | [requests](runs/project-2/requests-admin-on.json), [after](runs/project-2/after-admin-on.json), [diff](runs/project-2/diff-admin-on.md) |

Também conferido:

- Admin ligado sem token retorna 401.
- O log do servidor mostra só os 4 últimos dígitos do cartão e não mostra a chave do gateway.
- Não sobrou nenhuma credencial nem o default `"123456"` em `src/`.

`scripts/smoke.py` ganhou o campo opcional `headers` por chamada, para testar com o token.

Mudanças intencionais de contrato listadas pela skill, fora do smoke:

- Checkout com e-mail existente e senha errada retorna 401.
- Usuário novo sem `pwd` retorna 400.
- Tipos inválidos retornam 400.
- `DELETE` de id inexistente retorna 404.

## Projeto 3: resultado das Fases 1–2

Rodado desacoplado da sessão (`fork` + `setsid`), com a skill copiada sem alteração (`diff -r` vazio).

| Critério            | Resultado                                                                                                                                                                                                                                                                   |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Stack detectada     | Python 3.13 + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1, além de dependências sem uso (marshmallow, requests, python-dotenv)                                                                                                                                                     |
| Domínio             | Gerenciador de tarefas (usuários, categorias, relatórios)                                                                                                                                                                                                                   |
| Arquitetura         | Camadas parciais: `models/` existe, mas as rotas fazem consulta e regra; `services/` e `utils/` não são usados                                                                                                                                                              |
| Rotas inventariadas | 22, o mesmo total da linha de base, sem contar `/` e `/health`, que a skill também listou                                                                                                                                                                                   |
| Findings            | 14: CRITICAL 4, HIGH 3, MEDIUM 5, LOW 2                                                                                                                                                                                                                                     |
| Linhas              | Amostra conferida (`app.py:13`, `15`, `34`; `models/user.py:21`, `27-32`; `user_routes.py:52`, `71-72`, `119-122`, `140-142`, `209-210`; `notification_service.py:7-10`; `report_routes.py:163`, `196-197`; `task_routes.py:31`, `42`, `62-63`, `113`, `261`): todas exatas |
| Pausa               | Terminou em `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`. O `git status` mostrou só o relatório, o log e a cópia da skill                                                                                                                                  |

Em relação à análise manual:

- Os 13 itens foram encontrados, inclusive o cadastro anônimo de `admin`, como CRITICAL (AP-15).
- O hash vazado foi citado exatamente nas 4 rotas certas (`user_routes.py:33`, `85`, `129`, `209`).
- O AP-10 lista todas as chamadas de `utcnow` e `Query.get`.
- Não marcou AP-02 (o `.like()` do ORM é parametrizado), AP-03 nem AP-06 (a lista de notificações pertence a uma
  instância nunca usada). Isso está correto.

## Projeto 3: resultado da Fase 3

A execução rodou desacoplada e de uma vez só. A skill manteve `models/` e os blueprints, sem reescrever do zero.
Acrescentou `config/`, `controllers/`, `services/`, `serializers/`, `middlewares/` e `utils/` (scrypt e um `utcnow`
moderno), além de um blueprint de categorias. Removeu o código morto (`notification_service.py`, que tinha a senha SMTP,
e `helpers.py`) e tirou do `requirements.txt` as duas dependências sem uso. Deu ✗ em "Zero anti-patterns remaining", com
a justificativa de que o token de login continua falso: autenticação real mudaria o contrato.

**Verificação externa** (`seed.py`, `PORT=5001 python app.py`, `smoke.py` e `compare.py`):

| Execução                                     | Divergências                                                                                                                        | Arquivos                                                                                                                                |
|----------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| Padrão (admin desligado)                     | 13, intencionais: 4 sem o campo `password` (detalhe, criar, atualizar, login) e 9 rotas de exclusão e relatório que passam para 403 | [after](runs/project-3/after.json), [diff](runs/project-3/diff.md), [server](runs/project-3/after-server.log)                           |
| `ENABLE_ADMIN_ROUTES=true` + `X-Admin-Token` | 4, só a remoção do `password`. Os valores conferidos com `--valores` (contagens, `completion_rate`, mensagens) batem com o original | [requests](runs/project-3/requests-admin-on.json), [after](runs/project-3/after-admin-on.json), [diff](runs/project-3/diff-admin-on.md) |

Checagens manuais:

- Relatório sem token retorna 401.
- `POST /users` com `role: admin` sem token retorna 403.
- Login com a senha do seed retorna 200, sem o hash.
- Não sobrou nenhum `utcnow()` antigo, `Query.get`, MD5, `except:` nu nem segredo. Os `print` que restam estão só no
  `seed.py`, que é CLI.

A skill deixou o app original no ar na porta 5001, porque o `kill` foi negado no headless. Como no projeto 1, encerrei à
mão.

## Fechamento

- As 3 cópias da skill são idênticas (`diff -r` vazio).
- O enunciado original foi movido para [`docs/ENUNCIADO.md`](ENUNCIADO.md). O [`README.md`](../README.md) passou a ser a
  documentação da entrega, com as seções A) Análise Manual, B) Construção da Skill, C) Resultados (com o checklist
  preenchido para os 3 projetos) e D) Como Executar.
- O `CLAUDE.md` da raiz foi restaurado e continua no `.gitignore`.

## Próximo passo (rodada 1)

1. `git push` do fork, com confirmação do usuário.
2. Atualizar o repositório `mba` (`README.md` e `docs/contexto/decisoes.md`) com o status e o link do handoff.

## Checklist de entrega (enunciado)

- [ ] Fork público de `mba-ia-refactor-projects-skill`
- [x] `.claude/skills/refactor-arch/` idêntica nos 3 projetos, com `SKILL.md` e as 5 áreas de conhecimento
- [x] Catálogo com ≥ 8 anti-patterns (incluindo APIs deprecated): 15. Playbook com ≥ 8 transformações: 18.
- [x] Código refatorado dos 3 projetos commitado
- [x] `reports/audit-project-1.md`, `-2.md` e `-3.md` na raiz
- [x] Nos 3 projetos: stack detectada, ≥ 5 findings, ≥ 1 CRITICAL ou HIGH, aplicação no ar e endpoints respondendo
- [x] README com Análise Manual, Construção da Skill, Resultados e Como Executar
- [ ] URL do fork enviada na área de entrega da plataforma
