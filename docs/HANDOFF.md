# Handoff: Desafio 4 (skill `refactor-arch`)

Atualizado ao fim de cada etapa. O plano do desafio e o plano de execução ficam no repositório de planejamento, fora deste fork.

## Estado atual

**Os 3 projetos foram concluídos (Fases 1–3) e verificados por fora.** Próximo: fechamento (sincronizar a skill, escrever o README, restaurar o `CLAUDE.md` e fazer o push com confirmação).

| Etapa | Status | Artefato |
| --- | --- | --- |
| 0. Preparação | Feito | `docs/`, `scripts/`, [`reports/`](../reports/) |
| 1. Linha de base | Feito (P1, P2, P3) | [`docs/baseline/`](baseline/) |
| 2. Análise manual | Feito e revisado | [`docs/analise-manual.md`](analise-manual.md) |
| 3. Skill | v2 (pós-revisão) | [`code-smells-project/.claude/skills/refactor-arch/`](../code-smells-project/.claude/skills/refactor-arch/) |
| 3b. Revisão do checkpoint 1 | Feito | ver "Revisão do checkpoint 1" abaixo |
| 4. Projeto 1 | Feito (Fases 1–3 + verificação) | [relatório](../reports/audit-project-1.md), [log 1–2](runs/project-1/phase-1-2.log), [log 3](runs/project-1/phase-3.log), [after](runs/project-1/after.json), [diff](runs/project-1/diff.md), [server](runs/project-1/after-server.log) |
| 5. Projeto 2 | Feito (Fases 1–3 + verificação) | [relatório](../reports/audit-project-2.md), [log 1–2](runs/project-2/phase-1-2.log), [log 3](runs/project-2/phase-3.log), [diff](runs/project-2/diff.md), [diff admin ligado](runs/project-2/diff-admin-on.md) |
| 6. Projeto 3 | Feito (Fases 1–3 + verificação) | [relatório](../reports/audit-project-3.md), [log 1–2](runs/project-3/phase-1-2.log), [log 3](runs/project-3/phase-3.log), [diff](runs/project-3/diff.md), [diff admin ligado](runs/project-3/diff-admin-on.md) |
| 7. Fechamento e README | Pendente | — |

## Linha de base

Cada `requests-project-N.json` lista as chamadas, e cada `before-project-N.json` guarda o status e o corpo gravados no código **original**.

| Projeto | Chamadas | Porta | Status observados | Arquivos |
| --- | --- | --- | --- | --- |
| 1 (Flask) | 35 | 5001 | 200, 201, 400, 401, 404, 500 | [requests](baseline/requests-project-1.json), [before](baseline/before-project-1.json), [log](runs/project-1/baseline-server.log) |
| 2 (Express) | 7 | 3000 | 200, 400, 404 | [requests](baseline/requests-project-2.json), [before](baseline/before-project-2.json), [log](runs/project-2/baseline-server.log) |
| 3 (Flask + ORM) | 44 | 5001 | 200, 201, 400, 401, 404, 409 | [requests](baseline/requests-project-3.json), [before](baseline/before-project-3.json), [log](runs/project-3/baseline-server.log) |

Ferramentas:
- [`scripts/smoke.py`](../scripts/smoke.py) executa as chamadas.
- [`scripts/compare.py`](../scripts/compare.py) compara status e estrutura do corpo; com `--valores`, compara também os campos indicados.

### Como reproduzir (estado inicial obrigatório)

Os IDs das chamadas dependem do estado inicial do banco. **Antes de cada execução:**

| Projeto | Reset | Subir |
| --- | --- | --- |
| 1 | `rm -f code-smells-project/loja.db` (o `AUTOINCREMENT` não volta com `DELETE`) | `cd code-smells-project && .venv/bin/python -m flask --app app run -p 5001` |
| 2 | Reiniciar o processo (banco em memória) | `cd ecommerce-api-legacy && npm start` |
| 3 | `cd task-manager-api && .venv/bin/python seed.py` (o banco fica em `instance/tasks.db`) | `cd task-manager-api && .venv/bin/python -m flask --app app run -p 5001` |

```bash
python3 scripts/smoke.py docs/baseline/requests-project-1.json http://localhost:5001 /tmp/after-1.json
python3 scripts/compare.py docs/baseline/before-project-1.json /tmp/after-1.json
```

## Revisão do checkpoint 1

Três subagentes revisaram, cada um, uma parte do trabalho. O que foi corrigido:

- **Análise manual.** 10 itens com linha, descrição ou severidade errada. Exemplos:
  - SQL injection no P1 citava linhas protegidas pelo conversor `<int:>`.
  - No P3, o `GET /users` **não** vaza o hash; as rotas que vazam são outras quatro.
  - `datetime` **é** usado no `app.py` do P3.

  Também entraram 6 problemas que faltavam, como o cadastro anônimo de `admin` no P3 (CRITICAL). Foi adicionada a coluna AP, que liga cada item ao catálogo.
- **Skill:**
  - Catálogo: de 12 para 15 anti-patterns (duplicação, validação ausente, configuração insegura). A regra de severidade deixou de ser contraditória, e a Fase 2 passou a ser só leitura.
  - Playbook: de 15 para 18 transformações. Agora usa um domínio neutro, para não copiar código dos projetos. O T01 não derruba mais o boot sem `.env`. Entraram o adaptador callback → promise, o `asyncHandler`, um handler de erro que preserva 404/405 e um hash que não gera 500 com formato inválido.
  - `SKILL.md`: frontmatter YAML válido. O snapshot passou a usar reset de estado, diretório temporário fora do projeto e verificação de porta. Ficou uma ordem única de aplicação, e o checklist MVC do enunciado entrou na saída da Fase 3.
- **Scripts:**
  - `compare.py` agora trata erro de conexão como divergência, une os tipos de todos os itens de uma lista, considera `int` e `float` como "número", recusa IDs duplicados e aceita `--valores`.
  - `smoke.py` captura timeout e queda de conexão.

## Decisões e desvios

- **Porta 5000 ocupada no macOS (ControlCenter/AirPlay).** A primeira linha de base do P3 subiu na 5000 e recebeu 403 em tudo. Foi descartada e refeita na 5001.
- **A linha de base do Flask rodou com `flask run`, com debug desligado.** O original roda com `python app.py`, debug ligado. As respostas não mudam, porque todos os handlers capturam as exceções, mas a diferença fica registrada.
- **Comportamentos ruins preservados na linha de base, que a Fase 3 deve mudar de propósito:**
  - `POST /produtos` sem corpo devolve 500 (P1).
  - O checkout cria o usuário antes de validar o pagamento (P2).
  - `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `/login` devolvem o hash da senha (P3).
  - `/health` devolve a `secret_key` (P1).
- **O log de baseline do P2 contém o número de cartão de teste (`4111…`)** e a chave fictícia do gateway, porque o próprio código original os imprime (`AppManager.js:45`). São dados de teste do `api.http`, não dados reais.
- **Node 26.7:** o `sqlite3@5.1.6` compilou sem precisar do plano B.
- **O `CLAUDE.md` da raiz do fork está no `.gitignore`.** Ele vira `CLAUDE.md.off` durante as execuções headless, para não dar à skill informação sobre os projetos.
- **Comando headless:** `--add-dir ../reports`, porque o relatório é gravado fora do diretório do projeto.

## Projeto 1: resultado das Fases 1–2

Comando: `claude -p "/refactor-arch ../reports/audit-project-1.md" --add-dir ../reports --permission-mode acceptEdits --allowedTools "Read Glob Grep Write Edit Bash"`, rodado em `code-smells-project/` com o `CLAUDE.md` da raiz renomeado para `.off`.

| Critério | Resultado |
| --- | --- |
| Stack detectada | Python 3.13 (versão do `.venv`) + Flask 3.1.1, flask-cors 5.0.1, sqlite3 |
| Domínio | E-commerce (produtos, usuários/login, pedidos com estoque, relatório de vendas) |
| Arquivos | 4 (`app.py`, `controllers.py`, `database.py`, `models.py`), ~780 linhas |
| Rotas inventariadas | 19, o mesmo total da linha de base |
| Findings | 14: CRITICAL 4, HIGH 4, MEDIUM 4, LOW 2 |
| Cobertura da análise manual | 13 de 13 itens encontrados |
| Linhas | Amostra de 10 referências conferida contra o código: todas exatas |
| Pausa | Terminou em `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`; `git status` mostrou só o relatório e o log |

Divergências em relação à análise manual (decisões da skill, não erros):
- Classificou a arquitetura como "camadas parciais", e não como monolito, porque já existem `models.py` e `controllers.py`.
- Não marcou AP-03 (god module), porque nenhum arquivo junta as três responsabilidades. Pelo catálogo, esse caso vira AP-05, o mesmo critério da análise manual.
- Não encontrou API deprecated no projeto 1. Correto: o projeto 1 não usa nenhuma.

## Projeto 1: resultado da Fase 3

Comando: `claude -p --continue "sim, prossiga com a Fase 3" --add-dir ../reports --permission-mode acceptEdits --allowedTools "Read Glob Grep Write Edit Bash"`, em `code-smells-project/`. Saída em [`runs/project-1/phase-3.log`](runs/project-1/phase-3.log).

Estrutura nova: `app.py` (composição) + `config/`, `routes/`, `controllers/`, `services/`, `models/`, `serializers/`, `middlewares/`, `utils/`, `.env.example`. Os 4 arquivos originais saíram. O checklist MVC da skill deu ✓ em todos os itens; "Zero anti-patterns remaining" ficou ✗ e foi justificado (AP-07: o projeto não tem autenticação real, e criar uma quebraria o contrato; CORS `*` configurável).

**Verificação externa** (`rm -f loja.db`, `PORT=5001 python app.py`, `smoke.py` e `compare.py`): 35 chamadas, 7 divergências, todas intencionais ([diff](runs/project-1/diff.md)).

| Chamada | Antes → depois | Motivo |
| --- | --- | --- |
| `health` | formato | saem `secret_key`, `db_path` e `debug` (nenhum campo novo) |
| `usuarios-listar`, `usuarios-detalhe-ok` | formato | sai `senha` (nenhum campo novo) |
| `produtos-criar-400-sem-body` | 500 → 400 | validação na borda |
| `admin-query-select`, `admin-query-400`, `admin-reset-db` | 200/400 → 403 | admin desligado por padrão |

Checagens manuais extras:
- Com `ENABLE_ADMIN_ROUTES=true ADMIN_TOKEN=…`: `/admin/query` sem token → 401, com token → 200 (`COUNT(*) = 10`); `/admin/reset-db` com token → 200.
- `POST /login` com `admin@loja.com`/`admin123` → 200, com senha agora em scrypt.
- Nenhum SQL concatenado com valor do cliente sobrou (os dois f-strings restantes montam só nomes fixos de tabela e marcadores `?`). Nenhum `print`. Log do servidor sem erro.

Observações:
- A skill deixou o app original rodando na porta 5050 (o `kill` foi negado no modo headless). Encerrei os processos à mão. Nos próximos projetos, conferir `lsof` depois da Fase 3.
- A skill também atualizou o `README.md` do projeto (estrutura, configuração e rotas de admin).
- O material de trabalho da skill ficou em um diretório temporário fora do repositório, como pede o `SKILL.md`.

## Projeto 2: resultado das Fases 1–2

Mesmo comando, em `ecommerce-api-legacy/`, com a skill copiada sem alteração (`diff -r` vazio).

| Critério | Resultado |
| --- | --- |
| Stack detectada | JavaScript (Node 26.7) + Express 4.22.1, sqlite3 5.1.7 em memória |
| Domínio | LMS com checkout (cursos, matrícula, pagamento, relatório financeiro) |
| Arquitetura | Monolito (`AppManager.js` junta schema, seed, regras e rotas) |
| Rotas inventariadas | 3 (`POST /api/checkout`, `GET /api/admin/financial-report`, `DELETE /api/users/:id`) |
| Findings | 13: CRITICAL 4, HIGH 4, MEDIUM 3, LOW 2 |
| Linhas | Amostra conferida (`utils.js:2-5`, `17-23`; `AppManager.js:18`, `45`, `68`, `92`, `104`, `106`, `131-136`): todas exatas |
| Pausa | Terminou em `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`; `git status` mostrou só o relatório, o log e a cópia da skill |

Em relação à análise manual:
- Todos os itens das tabelas foram encontrados. A skill marcou AP-03 (god class) como CRITICAL, o que a análise manual também faz.
- A skill encontrou ainda a senha em texto puro no seed (`AppManager.js:18`).
- Ficou implícito: o checkout cria o usuário **antes** de validar o pagamento. O relatório cobre o fluxo pelo AP-05, mas não cita isso como problema à parte.
- Não marcou AP-02 (todas as queries usam `?`) nem AP-10. Correto.

## Projeto 2: resultado da Fase 3

Estrutura nova em `src/`: `app.js` (composição), `config/`, `models/` (adaptador Promise sobre o driver de callback + um model por tabela), `services/`, `controllers/`, `routes/`, `middlewares/` (`asyncHandler`, `errorHandler`, `adminGuard`), `errors/`, `utils/`, além do `.env.example`. `AppManager.js` e `utils.js` foram removidos. A skill marcou ✓ em todo o checklist, inclusive "Zero anti-patterns remaining".

**Execução interrompida duas vezes.** O `claude -p` rodava como job em background desta sessão e morreu junto com ela: na 1ª vez logo depois do snapshot, na 2ª no meio da refatoração. A 3ª execução rodou desacoplada (`fork` + `setsid`) e retomou a mesma sessão com `--continue`, partindo do código parcial e do snapshot. O [log da Fase 3](runs/project-2/phase-3.log) registra só essa última execução. Para o projeto 3, rodar desacoplado desde o início.

**Verificação externa** (`node src/app.js`, porta 3000, banco em memória, `smoke.py` e `compare.py`):

| Execução | Divergências | Arquivos |
| --- | --- | --- |
| Padrão (admin desligado) | 2, intencionais: `relatorio-financeiro` e `usuario-deletar` 200 → 403 | [after](runs/project-2/after.json), [diff](runs/project-2/diff.md), [server](runs/project-2/after-server.log) |
| `ENABLE_ADMIN_ROUTES=true` + `X-Admin-Token` | 0; o relatório saiu com os **mesmos valores** do original | [requests](runs/project-2/requests-admin-on.json), [after](runs/project-2/after-admin-on.json), [diff](runs/project-2/diff-admin-on.md) |

Também conferido:
- Admin ligado sem token → 401.
- O log do servidor mostra só os 4 últimos dígitos do cartão e não mostra a chave do gateway.
- Não sobrou nenhuma credencial nem o default `"123456"` em `src/`.

`scripts/smoke.py` ganhou o campo opcional `headers` por chamada, para testar com o token.

Mudanças intencionais de contrato listadas pela skill, fora do smoke:
- Checkout com e-mail existente e senha errada → 401.
- Usuário novo sem `pwd` → 400.
- Tipos inválidos → 400.
- `DELETE` de id inexistente → 404.

## Projeto 3: resultado das Fases 1–2

Rodado desacoplado da sessão (`fork` + `setsid`), com a skill copiada sem alteração (`diff -r` vazio).

| Critério | Resultado |
| --- | --- |
| Stack detectada | Python 3.13 + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (e dependências sem uso: marshmallow, requests, python-dotenv) |
| Domínio | Gerenciador de tarefas (usuários, categorias, relatórios) |
| Arquitetura | Camadas parciais (`models/` existe; as rotas fazem consulta e regra; `services/` e `utils/` não são usados) |
| Rotas inventariadas | 22, o mesmo total da linha de base, sem contar `/` e `/health`, que a skill também listou |
| Findings | 14: CRITICAL 4, HIGH 3, MEDIUM 5, LOW 2 |
| Linhas | Amostra conferida (`app.py:13`, `15`, `34`; `models/user.py:21`, `27-32`; `user_routes.py:52`, `71-72`, `119-122`, `140-142`, `209-210`; `notification_service.py:7-10`; `report_routes.py:163`, `196-197`; `task_routes.py:31`, `42`, `62-63`, `113`, `261`): todas exatas |
| Pausa | Terminou em `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`; `git status` mostrou só o relatório, o log e a cópia da skill |

Em relação à análise manual:
- Os 13 itens foram encontrados, inclusive o cadastro anônimo de `admin`, como CRITICAL (AP-15).
- O hash vazado foi citado exatamente nas 4 rotas certas (`user_routes.py:33`, `85`, `129`, `209`).
- O AP-10 lista todas as chamadas de `utcnow` e `Query.get`.
- Não marcou AP-02 (`.like()` do ORM é parametrizado), AP-03 nem AP-06 (a lista de notificações pertence a uma instância nunca usada). Correto.

## Projeto 3: resultado da Fase 3

Rodou desacoplado e de uma vez só. A skill manteve `models/` e os blueprints, sem reescrever do zero. Acrescentou `config/`, `controllers/`, `services/`, `serializers/`, `middlewares/` e `utils/` (scrypt e um `utcnow` moderno), e um blueprint de categorias. Removeu o código morto (`notification_service.py`, que tinha a senha SMTP, e `helpers.py`) e tirou do `requirements.txt` as duas dependências sem uso. Ela deu ✗ em "Zero anti-patterns remaining", com a justificativa de que o token de login continua falso: autenticação real mudaria o contrato.

**Verificação externa** (`seed.py`, `PORT=5001 python app.py`, `smoke.py` e `compare.py`):

| Execução | Divergências | Arquivos |
| --- | --- | --- |
| Padrão (admin desligado) | 13, intencionais: 4 sem o campo `password` (detalhe, criar, atualizar, login) + 9 rotas de exclusão e relatório → 403 | [after](runs/project-3/after.json), [diff](runs/project-3/diff.md), [server](runs/project-3/after-server.log) |
| `ENABLE_ADMIN_ROUTES=true` + `X-Admin-Token` | 4, só a remoção do `password`. Os valores conferidos com `--valores` (contagens, `completion_rate`, mensagens) batem com o original | [requests](runs/project-3/requests-admin-on.json), [after](runs/project-3/after-admin-on.json), [diff](runs/project-3/diff-admin-on.md) |

Checagens manuais:
- Relatório sem token → 401.
- `POST /users` com `role: admin` sem token → 403.
- Login com a senha do seed → 200, sem o hash.
- Sobraram zero `utcnow()` antigos, `Query.get`, MD5, `except:` nu e segredos (os `print` que restam estão só no `seed.py`, que é CLI).

A skill deixou o app original no ar na 5001 (o `kill` foi negado no headless), igual ao projeto 1. Encerrei à mão.

## Próximo passo

Fechamento:
1. Conferir `diff -r` das 3 cópias da skill.
2. README com Análise Manual, Construção da Skill, Resultados e Como Executar.
3. Restaurar o `CLAUDE.md`.
4. Push, com confirmação.
5. Atualizar o repositório `mba`.

## Checklist de entrega (enunciado)

- [ ] Fork público de `mba-ia-refactor-projects-skill`
- [ ] `.claude/skills/refactor-arch/` idêntica nos 3 projetos, com `SKILL.md` e as 5 áreas de conhecimento
- [x] Catálogo com ≥ 8 anti-patterns (incluindo APIs deprecated): 15. Playbook com ≥ 8 transformações: 18.
- [x] Código refatorado dos 3 projetos commitado
- [x] `reports/audit-project-1.md`, `-2.md` e `-3.md` na raiz
- [x] Nos 3 projetos: stack detectada, ≥ 5 findings, ≥ 1 CRITICAL ou HIGH, aplicação no ar e endpoints respondendo
- [ ] README com Análise Manual, Construção da Skill, Resultados e Como Executar
- [ ] URL do fork enviada na área de entrega da plataforma
